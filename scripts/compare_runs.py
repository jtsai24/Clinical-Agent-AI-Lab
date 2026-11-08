"""Print a comparison table across every saved run in output/runs/."""

import json
from pathlib import Path


def load_runs(runs_dir: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(runs_dir.glob("*.json"))]


def main() -> None:
    runs = load_runs(Path("output/runs"))
    if not runs:
        print("No runs found in output/runs/.")
        return

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


if __name__ == "__main__":
    main()
