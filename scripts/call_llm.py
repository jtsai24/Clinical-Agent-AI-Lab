"""Call the LLM on one PubMedQA row and record the raw response, for manual inspection
before any parsing/validation/scoring logic gets built (see PLAN.md)."""

import json
import os
from pathlib import Path

from datasets import load_dataset
from dotenv import load_dotenv
from together import Together

from validate import validate

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


def call_llm(question: str, context: dict) -> str:
    load_dotenv()
    prompt = build_prompt(question, context)
    #print(f"Prompt: {prompt}")
    client = Together(api_key=os.environ["MODEL_API_KEY"])
    response = client.chat.completions.create(
        model=os.environ["MODEL_NAME"],
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def main() -> None:
    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")["train"]
    row = labeled[0]

    raw_response = call_llm(row["question"], row["context"])
    result = validate(raw_response, row["context"])

    print(f"pubid: {row['pubid']}")
    print(f"question: {row['question']}")
    print(f"final_decision (gold label): {row['final_decision']}")
    print()
    print("raw LLM response:")
    print(raw_response)
    print()
    print(f"validation result: {result}")

    output_dir = Path("output/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "pubid": row["pubid"],
        "question": row["question"],
        "final_decision": row["final_decision"],
        "raw_response": raw_response,
        **result,
    }
    out_path = output_dir / f"{row['pubid']}.json"
    out_path.write_text(json.dumps(record, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
