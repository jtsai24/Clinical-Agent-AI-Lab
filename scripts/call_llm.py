"""Call the LLM on one PubMedQA row and record the raw response, for manual inspection
before any parsing/validation/scoring logic gets built (see PLAN.md)."""

import json
import os
from pathlib import Path

from datasets import load_dataset
from dotenv import load_dotenv
from together import Together

from validate import aggregate, score, validate

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


def call_llm(question: str, context: dict) -> str:
    load_dotenv()          # non-secret config: MODEL_PROVIDER, MODEL_BASE_URL, MODEL_NAME
    load_dotenv(".env.secret")  # MODEL_API_KEY only — kept separate so editing model config never requires reading the key file
    prompt = build_prompt(question, context)
    #print(f"Prompt: {prompt}")
    client = Together(api_key=os.environ["MODEL_API_KEY"])
    response = client.chat.completions.create(
        model=os.environ["MODEL_NAME"],
        temperature=0,
        max_tokens=2048,  # reasoning models (e.g. gpt-oss) burn tokens on hidden reasoning before the final answer
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def process_row(row: dict) -> dict:
    raw_response = call_llm(row["question"], row["context"])
    result = validate(raw_response, row["context"])
    record = {
        "pubid": row["pubid"],
        "question": row["question"],
        "final_decision": row["final_decision"],
        "raw_response": raw_response,
        **result,
    }
    return score(record, row["final_decision"])


def main() -> None:
    labeled = load_dataset("qiaojin/PubMedQA", "pqa_labeled")["train"]
    rows = labeled.select(range(ROW_COUNT))

    output_dir = Path("output/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for row in rows:
        record = process_row(row)
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

    report_path = Path("output/report.json")
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nSaved aggregate report to {report_path}")


if __name__ == "__main__":
    main()
