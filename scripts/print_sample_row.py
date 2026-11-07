"""Print one row from pqa_labeled, for manual inspection before wiring up the LLM call."""

from datasets import load_dataset


def main() -> None:
    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")["train"]
    row = labeled[0]

    print(f"pubid: {row['pubid']}")
    print(f"question: {row['question']}")
    print(f"context sections: {row['context']['labels']}")
    print("context (what Stage 1 gives the LLM, conclusion withheld):")
    for label, text in zip(row["context"]["labels"], row["context"]["contexts"]):
        print(f"  [{label}] {text}")
    print(f"long_answer (withheld conclusion): {row['long_answer']}")
    print(f"final_decision (gold label): {row['final_decision']}")


if __name__ == "__main__":
    main()
