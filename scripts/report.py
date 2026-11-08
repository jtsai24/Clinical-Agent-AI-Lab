"""Summarize a batch of validated and scored records into an aggregate report.

Pure function, no I/O. See PLAN.md's Outputs section.
"""


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

    total_latency_seconds = sum(r["latency_seconds"] for r in records)
    total_cost_usd = sum(r["cost_usd"] for r in records)

    return {
        "total_in": total_in,
        "valid_count": len(valid),
        "rejected_count": len(rejected),
        "rejected_by_reason": rejected_by_reason,
        "accuracy": accuracy,
        "mismatches": mismatches,
        "total_latency_seconds": total_latency_seconds,
        "avg_latency_seconds": total_latency_seconds / total_in if total_in else None,
        "total_cost_usd": total_cost_usd,
    }
