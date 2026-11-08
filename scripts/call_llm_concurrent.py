"""Run Stage 1 end to end on a slice of PubMedQA rows, concurrently: call the LLM,
validate and score each response, and write per-row and aggregate reports (see #16).
Row-processing logic lives in llm_pipeline.py (#21); this is CLI/orchestration only."""

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # dataset is already cached by download_data.py; skip the Hub rate-limit check

from datasets import load_dataset
from dotenv import load_dotenv
from together import Together

from aggregate import aggregate
from llm_pipeline import run_row_safe
from pricing import get_model_pricing

DEFAULT_ROW_COUNT = 10
DEFAULT_MAX_WORKERS = 5


def print_progress(record: dict) -> None:
    print(f"pubid: {record['pubid']} | status: {record['status']}", end="")
    if record["status"] == "valid":
        print(f" | answer: {record['answer']} | final_decision: {record['final_decision']} | correct: {record['correct']}")
    elif record["status"] == "rejected":
        print(f" | reject_reason: {record['reject_reason']}")
    else:
        print(f" | error_type: {record['error_type']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument("--model", type=str, default=None, help="overrides MODEL_NAME from .env")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_started_at = datetime.now(timezone.utc)
    load_dotenv()          # non-secret config: MODEL_PROVIDER, MODEL_BASE_URL, MODEL_NAME
    load_dotenv(".env.secret")  # MODEL_API_KEY only — kept separate so editing model config never requires reading the key file
    api_key = os.environ["MODEL_API_KEY"]
    model_name = args.model or os.environ["MODEL_NAME"]
    client = Together(api_key=api_key)
    pricing = get_model_pricing(model_name, api_key)

    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")["train"]
    rows = labeled.select(range(args.rows))

    output_dir = Path("output/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    wall_clock_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run_row_safe, client, model_name, row, pricing) for row in rows]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print_progress(record)
            out_path = output_dir / f"{record['pubid']}.json"
            out_path.write_text(json.dumps(record, indent=2))
    wall_clock_seconds = time.monotonic() - wall_clock_start

    records.sort(key=lambda r: r["pubid"])  # as_completed() yields out of row order

    report = aggregate(records)
    print()
    print("=== Aggregate report ===")
    print(json.dumps(report, indent=2))

    run = {
        "model": model_name,
        "started_at": run_started_at.isoformat(),
        "row_count": args.rows,
        "max_workers": args.workers,
        "wall_clock_seconds": wall_clock_seconds,
        "report": report,
        "records": records,
    }
    runs_dir = Path("output/runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    safe_model_name = model_name.replace("/", "_")
    run_path = runs_dir / f"{run_started_at.strftime('%Y-%m-%dT%H-%M-%S')}_{safe_model_name}.json"
    run_path.write_text(json.dumps(run, indent=2))
    print(f"\nSaved run to {run_path}")


if __name__ == "__main__":
    main()
