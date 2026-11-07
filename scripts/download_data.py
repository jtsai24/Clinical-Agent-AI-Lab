"""Download the three PubMedQA subsets and cache them locally via Hugging Face `datasets`."""

from datasets import load_dataset


def main() -> None:
    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")["train"]
    artificial = load_dataset("qiaojin/PubMedQA", "pqa_artificial")["train"]
    unlabeled = load_dataset("qiaojin/PubMedQA", "pqa_unlabeled")["train"]

    print(f"pqa_labeled:    {len(labeled)} rows")
    print(f"pqa_artificial: {len(artificial)} rows")
    print(f"pqa_unlabeled:  {len(unlabeled)} rows")
    print()
    print("Sample row from pqa_labeled:")
    print(labeled[0])


if __name__ == "__main__":
    main()
