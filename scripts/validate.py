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
