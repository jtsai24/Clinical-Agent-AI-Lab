"""Compare a validated record's answer to the gold label.

Pure function, no I/O. See PLAN.md's Process section, step 4.
"""


def score(record: dict, final_decision: str) -> dict:
    """Compare a valid record's answer to the gold label.

    No-op on rejected records: a rejected row is never counted as correct
    or incorrect (see PLAN.md's "What 'correct' means").
    """
    if record["status"] != "valid":
        return record
    return {**record, "correct": record["answer"] == final_decision.strip().lower()}
