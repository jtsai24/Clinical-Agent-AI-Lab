"""Validate the LLM's raw response for one PubMedQA row.

Pure functions only: no I/O, no network calls, no dataset loading.
See PLAN.md's Process section and issue #9 for the checks and their order.
"""

import json

VALID_ANSWERS = {"yes", "no", "maybe"}

# A quote at or above this fraction of the full abstract's length is treated
# as "basically everything" rather than a specific citation.
TRIVIAL_QUOTE_LENGTH_RATIO = 0.9


def _full_abstract_text(context: dict) -> str:
    return " ".join(context.get("contexts") or [])


def validate(raw_response: str, context: dict) -> dict:
    """Check context presence, then the LLM's raw_response, in order.

    Returns {"status": "rejected", "reject_reason": <code>} on the first
    failing check, or {"status": "valid", "answer": ..., "evidence_quote": ...}
    if all checks pass. Does not compare against final_decision — that's
    scoring, a separate step.
    """
    abstract = _full_abstract_text(context)
    if not abstract.strip():
        return {"status": "rejected", "reject_reason": "missing_context"}

    try:
        parsed = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {"status": "rejected", "reject_reason": "malformed_json"}

    if not isinstance(parsed, dict) or "answer" not in parsed or "evidence_quote" not in parsed:
        return {"status": "rejected", "reject_reason": "malformed_json"}

    answer = parsed["answer"]
    evidence_quote = parsed["evidence_quote"]
    if not isinstance(answer, str) or not isinstance(evidence_quote, str):
        return {"status": "rejected", "reject_reason": "malformed_json"}

    if answer.strip().lower() not in VALID_ANSWERS:
        return {"status": "rejected", "reject_reason": "invalid_answer"}

    quote = evidence_quote.strip()
    if not quote or len(quote) >= TRIVIAL_QUOTE_LENGTH_RATIO * len(abstract.strip()):
        return {"status": "rejected", "reject_reason": "trivial_quote"}

    # fabricated_quote check deferred — see issue #9.

    return {
        "status": "valid",
        "answer": answer.strip().lower(),
        "evidence_quote": quote,
    }


def score(record: dict, final_decision: str) -> dict:
    """Compare a valid record's answer to the gold label.

    No-op on rejected records: a rejected row is never counted as correct
    or incorrect (see PLAN.md's "What 'correct' means").
    """
    if record["status"] != "valid":
        return record
    return {**record, "correct": record["answer"] == final_decision.strip().lower()}


def aggregate(records: list[dict]) -> dict:
    """Summarize a batch of validated (and scored, for valid rows) records.

    Row accounting must reconcile: in == valid + rejected.
    """
    total_in = len(records)
    valid = [r for r in records if r["status"] == "valid"]
    rejected = [r for r in records if r["status"] == "rejected"]

    rejected_by_reason: dict = {}
    for r in rejected:
        reason = r["reject_reason"]
        rejected_by_reason[reason] = rejected_by_reason.get(reason, 0) + 1

    correct_count = sum(1 for r in valid if r["correct"])
    accuracy = correct_count / len(valid) if valid else None

    mismatches = [
        {"pubid": r["pubid"], "answer": r["answer"], "final_decision": r["final_decision"]}
        for r in valid
        if not r["correct"]
    ]

    return {
        "total_in": total_in,
        "valid_count": len(valid),
        "rejected_count": len(rejected),
        "rejected_by_reason": rejected_by_reason,
        "accuracy": accuracy,
        "mismatches": mismatches,
    }
