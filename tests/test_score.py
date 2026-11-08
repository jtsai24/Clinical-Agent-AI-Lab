from score import score


def test_valid_record_correct_answer():
    record = {"status": "valid", "answer": "yes", "evidence_quote": "..."}
    result = score(record, final_decision="yes")
    assert result["correct"] is True


def test_valid_record_wrong_answer():
    record = {"status": "valid", "answer": "no", "evidence_quote": "..."}
    result = score(record, final_decision="yes")
    assert result["correct"] is False


def test_rejected_record_is_noop():
    record = {"status": "rejected", "reject_reason": "invalid_answer"}
    result = score(record, final_decision="yes")
    assert result == record
    assert "correct" not in result
