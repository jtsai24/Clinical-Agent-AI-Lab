"""Print a comparison table across every saved run in output/runs/, plus a
per-model accuracy-over-time sparkline (rows run count differs per point, so
it's a trend, not a controlled comparison)."""

import json
from itertools import groupby
from pathlib import Path

SPARK_LEVELS = "▁▂▃▄▅▆▇█"


def load_runs(runs_dir: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(runs_dir.glob("*.json"))]


def sparkline(accuracies: list[float]) -> str:
    if not accuracies:
        return ""
    lo, hi = min(accuracies), max(accuracies)
    span = hi - lo
    return "".join(
        SPARK_LEVELS[int((a - lo) / span * (len(SPARK_LEVELS) - 1))] if span else SPARK_LEVELS[-1]
        for a in accuracies
    )


def print_table(runs: list[dict]) -> None:
    header = f"{'model':<35} {'started_at':<22} {'rows':>5} {'accuracy':>9} {'avg_latency_s':>14} {'total_cost_usd':>15}"
    print(header)
    print("-" * len(header))
    for run in runs:
        report = run["report"]
        accuracy = report["accuracy"]
        accuracy_str = f"{accuracy:.2f}" if accuracy is not None else "n/a"
        print(
            f"{run['model']:<35} {run['started_at']:<22} {run['row_count']:>5} "
            f"{accuracy_str:>9} {report['avg_latency_seconds']:>14.2f} {report['total_cost_usd']:>15.6f}"
        )


def print_trends(runs: list[dict]) -> None:
    print("\nAccuracy trend by model (chronological, low -> high within each model's own range; label = rows per point):")
    for model, group in groupby(sorted(runs, key=lambda r: r["model"]), key=lambda r: r["model"]):
        model_runs = sorted(group, key=lambda r: r["started_at"])
        accuracies = [r["report"]["accuracy"] for r in model_runs if r["report"]["accuracy"] is not None]
        rows_label = ",".join(str(r["row_count"]) for r in model_runs)
        print(f"  {model:<35} {sparkline(accuracies)}  (rows: {rows_label})")


def main() -> None:
    runs = load_runs(Path("output/runs"))
    if not runs:
        print("No runs found in output/runs/.")
        return

    print_table(runs)
    print_trends(runs)


if __name__ == "__main__":
    main()
