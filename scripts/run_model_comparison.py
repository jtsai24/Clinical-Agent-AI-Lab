"""Run call_llm_concurrent.py once per model in MODELS, same row slice, so their
output/runs/ reports become directly comparable via compare_runs.py. One model
failing (bad model id, rate limit, etc.) doesn't abort the rest of the sweep."""

import argparse
import subprocess
import sys

MODELS = [
    "deepseek-ai/DeepSeek-V4.1-Flash-1017",
    "zai-org/GLM-5.3-Flash",
    "zai-org/GLM-5.3",
    "moonshotai/Kimi-K3.1-Pro",
    "openai/gpt-oss-120b",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--workers", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = []
    for model in MODELS:
        print(f"\n=== {model} ===")
        result = subprocess.run(
            [
                sys.executable, "scripts/call_llm_concurrent.py",
                "--model", model,
                "--rows", str(args.rows),
                "--workers", str(args.workers),
            ]
        )
        if result.returncode != 0:
            failures.append(model)
            print(f"!! {model} failed (exit code {result.returncode}), continuing with the rest")

    print("\n=== Sweep done ===")
    if failures:
        print(f"Failed: {', '.join(failures)}")
    print("Run `python scripts/compare_runs.py` to see the comparison.")


if __name__ == "__main__":
    main()
