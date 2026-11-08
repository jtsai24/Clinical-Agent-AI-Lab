"""Run Stage 1 end to end on a slice of PubMedQA rows: call the LLM, validate
and score each response, and write per-row and aggregate reports (see PLAN.md)."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # dataset is already cached by download_data.py; skip the Hub rate-limit check

from datasets import load_dataset
from dotenv import load_dotenv
from together import Together

from cost import compute_cost
from pricing import get_model_pricing
from report import aggregate
from score import score
from validate import validate

ROW_COUNT = 10

PROMPT_TEMPLATE = """You are given a biomedical research question and the abstract of a paper \
(with its conclusion removed). Based only on the abstract, answer the question.

Question: {question}

Abstract:
{context}

Respond with ONLY a JSON object, no other text, in exactly this form:
{{"answer": "yes" | "no" | "maybe", "evidence_quote": "<the exact sentence from the abstract that most supports your answer>"}}
"""


def build_prompt(question: str, context: dict) -> str:
    abstract = "\n".join(
        f"[{label}] {text}"
        for label, text in zip(context["labels"], context["contexts"])
    )
    return PROMPT_TEMPLATE.format(question=question, context=abstract)


def call_llm(client: Together, question: str, context: dict) -> dict:
    prompt = build_prompt(question, context)
    start = time.monotonic()
    response = client.chat.completions.create(
        model=os.environ["MODEL_NAME"],
        temperature=0,
        max_tokens=2048,  # reasoning models (e.g. gpt-oss) burn tokens on hidden reasoning before the final answer
        messages=[{"role": "user", "content": prompt}],
    )
    latency_seconds = time.monotonic() - start
    return {
        "content": response.choices[0].message.content,
        "latency_seconds": latency_seconds,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
    }


def process_row(client: Together, row: dict, pricing: dict) -> dict:
    call_result = call_llm(client, row["question"], row["context"])
    result = validate(call_result["content"], row["context"])
    cost_usd = compute_cost(call_result["prompt_tokens"], call_result["completion_tokens"], pricing)
    record = {
        "pubid": row["pubid"],
        "question": row["question"],
        "context": row["context"],
        "reasoning_required_pred": "".join(row["context"].get("reasoning_required_pred") or []),
        "final_decision": row["final_decision"],
        "raw_response": call_result["content"],
        "latency_seconds": call_result["latency_seconds"],
        "cost_usd": cost_usd,
        **result,
    }
    return score(record, row["final_decision"])


def main() -> None:
    run_started_at = datetime.now(timezone.utc)
    load_dotenv()          # non-secret config: MODEL_PROVIDER, MODEL_BASE_URL, MODEL_NAME
    load_dotenv(".env.secret")  # MODEL_API_KEY only — kept separate so editing model config never requires reading the key file
    api_key = os.environ["MODEL_API_KEY"]
    model_name = os.environ["MODEL_NAME"]
    client = Together(api_key=api_key)
    pricing = get_model_pricing(model_name, api_key)

    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")["train"]
    rows = labeled.select(range(ROW_COUNT))

    output_dir = Path("output/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for row in rows:
        record = process_row(client, row, pricing)
        records.append(record)

        print(f"pubid: {record['pubid']} | status: {record['status']}", end="")
        if record["status"] == "valid":
            print(f" | answer: {record['answer']} | final_decision: {record['final_decision']} | correct: {record['correct']}")
        else:
            print(f" | reject_reason: {record['reject_reason']}")

        out_path = output_dir / f"{record['pubid']}.json"
        out_path.write_text(json.dumps(record, indent=2))

    report = aggregate(records)
    print()
    print("=== Aggregate report ===")
    print(json.dumps(report, indent=2))

    run = {
        "model": model_name,
        "started_at": run_started_at.isoformat(),
        "row_count": ROW_COUNT,
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
