import httpx
import together

import call_llm_concurrent
from call_llm_concurrent import build_prompt, run_row_safe

ROW = {"pubid": 123}


def test_build_prompt_includes_question_and_labeled_sections():
    context = {
        "labels": ["BACKGROUND", "RESULTS"],
        "contexts": ["Some background text.", "Some results text."],
    }
    prompt = build_prompt("Is X true?", context)

    assert "Is X true?" in prompt
    assert "[BACKGROUND] Some background text." in prompt
    assert "[RESULTS] Some results text." in prompt


def test_run_row_safe_passes_through_process_row_result(monkeypatch):
    expected = {"pubid": 123, "status": "valid", "answer": "yes"}
    monkeypatch.setattr(call_llm_concurrent, "process_row", lambda client, model_name, row, pricing: expected)

    result = run_row_safe(client=None, model_name="m", row=ROW, pricing={})

    assert result == expected


def test_run_row_safe_catches_rate_limit_error(monkeypatch):
    response = httpx.Response(status_code=429, request=httpx.Request("POST", "https://api.together.xyz/v1/chat/completions"))
    error = together.RateLimitError("rate limited", response=response, body=None)

    def raise_rate_limit(client, model_name, row, pricing):
        raise error

    monkeypatch.setattr(call_llm_concurrent, "process_row", raise_rate_limit)

    result = run_row_safe(client=None, model_name="m", row=ROW, pricing={})

    assert result["pubid"] == 123
    assert result["status"] == "error"
    assert result["error_type"] == "rate_limited"
    assert result["error_message"] == "rate limited"
    assert result["cost_usd"] == 0.0
    assert result["latency_seconds"] >= 0


def test_run_row_safe_catches_other_exceptions(monkeypatch):
    def raise_value_error(client, model_name, row, pricing):
        raise ValueError("boom")

    monkeypatch.setattr(call_llm_concurrent, "process_row", raise_value_error)

    result = run_row_safe(client=None, model_name="m", row=ROW, pricing={})

    assert result["pubid"] == 123
    assert result["status"] == "error"
    assert result["error_type"] == "other"
    assert result["error_message"] == "boom"
    assert result["cost_usd"] == 0.0
