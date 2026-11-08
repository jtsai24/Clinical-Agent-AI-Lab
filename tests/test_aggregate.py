from aggregate import aggregate


def valid(pubid, answer, final_decision, correct, latency_seconds=1.0, cost_usd=0.001):
    return {
        "pubid": pubid,
        "status": "valid",
        "answer": answer,
        "final_decision": final_decision,
        "correct": correct,
        "latency_seconds": latency_seconds,
        "cost_usd": cost_usd,
    }


def rejected(pubid, reason, latency_seconds=1.0, cost_usd=0.001):
    return {
        "pubid": pubid,
        "status": "rejected",
        "reject_reason": reason,
        "latency_seconds": latency_seconds,
        "cost_usd": cost_usd,
    }


def errored(pubid, error_type, latency_seconds=1.0, cost_usd=0.0):
    return {
        "pubid": pubid,
        "status": "error",
        "error_type": error_type,
        "error_message": "boom",
        "latency_seconds": latency_seconds,
        "cost_usd": cost_usd,
    }


def test_row_accounting_reconciles():
    records = [
        valid(1, "yes", "yes", True),
        rejected(2, "malformed_json"),
        rejected(3, "invalid_answer"),
        errored(4, "rate_limited"),
    ]
    report = aggregate(records)
    assert report["total_in"] == 4
    assert report["valid_count"] + report["rejected_count"] + report["errored_count"] == report["total_in"]


def test_errored_by_type_counts():
    records = [
        errored(1, "rate_limited"),
        errored(2, "rate_limited"),
        errored(3, "other"),
    ]
    report = aggregate(records)
    assert report["errored_by_type"] == {"rate_limited": 2, "other": 1}
    assert report["accuracy"] is None


def test_rejected_by_reason_counts():
    records = [
        rejected(1, "malformed_json"),
        rejected(2, "malformed_json"),
        rejected(3, "invalid_answer"),
    ]
    report = aggregate(records)
    assert report["rejected_by_reason"] == {"malformed_json": 2, "invalid_answer": 1}


def test_accuracy_only_over_valid_rows():
    records = [
        valid(1, "yes", "yes", True),
        valid(2, "no", "yes", False),
        rejected(3, "fabricated_quote"),
    ]
    report = aggregate(records)
    assert report["accuracy"] == 0.5
    assert report["valid_count"] == 2


def test_mismatches_list_only_wrong_valid_rows():
    records = [
        valid(1, "yes", "yes", True),
        valid(2, "no", "yes", False),
    ]
    report = aggregate(records)
    assert report["mismatches"] == [{"pubid": 2, "answer": "no", "final_decision": "yes"}]


def test_accuracy_is_none_when_no_valid_rows():
    records = [rejected(1, "malformed_json")]
    report = aggregate(records)
    assert report["accuracy"] is None
    assert report["mismatches"] == []


def test_latency_and_cost_summed_over_all_rows_including_rejected():
    records = [
        valid(1, "yes", "yes", True, latency_seconds=2.0, cost_usd=0.01),
        rejected(2, "malformed_json", latency_seconds=1.0, cost_usd=0.005),
    ]
    report = aggregate(records)
    assert report["total_latency_seconds"] == 3.0
    assert report["avg_latency_seconds"] == 1.5
    assert report["total_cost_usd"] == 0.015
