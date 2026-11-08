import json

from validate import validate

CONTEXT = {
    "labels": ["BACKGROUND", "RESULTS"],
    "contexts": [
        "This study looks at whether X affects Y.",
        "X was found to significantly increase Y in all treated subjects.",
    ],
}


def valid_response(answer="yes", evidence_quote="X was found to significantly increase Y in all treated subjects."):
    return json.dumps({"answer": answer, "evidence_quote": evidence_quote})


def test_valid_response_passes():
    result = validate(valid_response(), CONTEXT)
    assert result == {
        "status": "valid",
        "answer": "yes",
        "evidence_quote": "X was found to significantly increase Y in all treated subjects.",
    }


def test_missing_context_checked_before_anything_else():
    empty_context = {"labels": [], "contexts": []}
    result = validate("not even valid json", empty_context)
    assert result == {"status": "rejected", "reject_reason": "missing_context"}


def test_malformed_json_not_parseable():
    result = validate("sure, here's the answer: yes", CONTEXT)
    assert result == {"status": "rejected", "reject_reason": "malformed_json"}


def test_malformed_json_missing_field():
    result = validate(json.dumps({"answer": "yes"}), CONTEXT)
    assert result == {"status": "rejected", "reject_reason": "malformed_json"}


def test_malformed_json_wrong_type():
    result = validate(json.dumps({"answer": "yes", "evidence_quote": 123}), CONTEXT)
    assert result == {"status": "rejected", "reject_reason": "malformed_json"}


def test_invalid_answer_outside_domain():
    result = validate(valid_response(answer="likely yes"), CONTEXT)
    assert result == {"status": "rejected", "reject_reason": "invalid_answer"}


def test_trivial_quote_empty():
    result = validate(valid_response(evidence_quote=""), CONTEXT)
    assert result == {"status": "rejected", "reject_reason": "trivial_quote"}


def test_trivial_quote_near_duplicate_of_whole_abstract():
    whole_abstract = " ".join(CONTEXT["contexts"])
    result = validate(valid_response(evidence_quote=whole_abstract), CONTEXT)
    assert result == {"status": "rejected", "reject_reason": "trivial_quote"}
