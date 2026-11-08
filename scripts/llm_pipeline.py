"""Pure LLM-calling and row-processing logic for Stage 1, split out from
call_llm_concurrent.py (#21) so unit tests can cover it without dragging in
CLI/orchestration concerns (argparse, dataset loading, file I/O) that are only
meaningfully exercised by actually running the pipeline."""

import time

import together
from together import Together

from cost import compute_cost
from score import score
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


def call_llm(client: Together, model_name: str, question: str, context: dict) -> dict:
    prompt = build_prompt(question, context)
    start = time.monotonic()
    response = client.chat.completions.create(
        model=model_name,
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


def process_row(client: Together, model_name: str, row: dict, pricing: dict) -> dict:
    call_result = call_llm(client, model_name, row["question"], row["context"])
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


def run_row_safe(client: Together, model_name: str, row: dict, pricing: dict) -> dict:
    """Never raises — any failure becomes a status: "error" record instead,
    so one row's failure can't crash the batch (see #16)."""
    start = time.monotonic()
    try:
        return process_row(client, model_name, row, pricing)
    except together.RateLimitError as e:
        error_type = "rate_limited"
        message = str(e)
    except Exception as e:
        error_type = "other"
        message = str(e)
    return {
        "pubid": row["pubid"],
        "status": "error",
        "error_type": error_type,
        "error_message": message,
        "latency_seconds": time.monotonic() - start,
        "cost_usd": 0.0,  # no tokens were charged — the call never returned a response
    }
