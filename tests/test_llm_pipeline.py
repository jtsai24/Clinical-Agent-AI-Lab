from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import together

import llm_pipeline
from llm_pipeline import build_prompt, call_llm, process_row, run_row_safe

ROW = {"pubid": 123}


def make_fake_client(content: str, prompt_tokens: int = 10, completion_tokens: int = 5) -> MagicMock:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )
    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


def test_build_prompt_includes_question_and_labeled_sections():
    context = {
        "labels": ["BACKGROUND", "RESULTS"],
        "contexts": ["Some background text.", "Some results text."],
    }
    prompt = build_prompt("Is X true?", context)

    assert "Is X true?" in prompt
    assert "[BACKGROUND] Some background text." in prompt
    assert "[RESULTS] Some results text." in prompt


def test_call_llm_sends_expected_request_and_parses_response():
    client = make_fake_client('{"answer": "yes", "evidence_quote": "quote"}', prompt_tokens=10, completion_tokens=5)
    context = {"labels": ["BACKGROUND"], "contexts": ["Some background text."]}

    result = call_llm(client, "gpt-test", "Is X true?", context)

    client.chat.completions.create.assert_called_once()
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-test"
    assert kwargs["temperature"] == 0
    assert kwargs["max_tokens"] == 2048
    assert "Is X true?" in kwargs["messages"][0]["content"]

    assert result["content"] == '{"answer": "yes", "evidence_quote": "quote"}'
    assert result["prompt_tokens"] == 10
    assert result["completion_tokens"] == 5
    assert result["latency_seconds"] >= 0


def test_process_row_assembles_record_from_valid_response():
    abstract = "Patients receiving the drug showed significant improvement. The control group showed no change."
    quote = "Patients receiving the drug showed significant improvement."
    client = make_fake_client(
        f'{{"answer": "yes", "evidence_quote": "{quote}"}}',
        prompt_tokens=100,
        completion_tokens=20,
    )
    row = {
        "pubid": 456,
        "question": "Did the drug help?",
        "context": {
            "labels": ["RESULTS"],
            "contexts": [abstract],
            "reasoning_required_pred": ["yes"],
        },
        "final_decision": "yes",
    }
    pricing = {"input": 1.0, "output": 2.0}

    record = process_row(client, "gpt-test", row, pricing)

    assert record["pubid"] == 456
    assert record["status"] == "valid"
    assert record["answer"] == "yes"
    assert record["correct"] is True
    assert record["reasoning_required_pred"] == "yes"
    assert record["cost_usd"] == (100 / 1_000_000) * 1.0 + (20 / 1_000_000) * 2.0


def test_process_row_rejects_malformed_response():
    client = make_fake_client("not json")
    row = {
        "pubid": 789,
        "question": "Did the drug help?",
        "context": {"labels": ["RESULTS"], "contexts": ["Some abstract text."]},
        "final_decision": "yes",
    }

    record = process_row(client, "gpt-test", row, {"input": 0.0, "output": 0.0})

    assert record["status"] == "rejected"
    assert record["reject_reason"] == "malformed_json"


def test_run_row_safe_passes_through_process_row_result(monkeypatch):
    expected = {"pubid": 123, "status": "valid", "answer": "yes"}
    monkeypatch.setattr(llm_pipeline, "process_row", lambda client, model_name, row, pricing: expected)

    result = run_row_safe(client=None, model_name="m", row=ROW, pricing={})

    assert result == expected


def test_run_row_safe_catches_rate_limit_error(monkeypatch):
    response = httpx.Response(status_code=429, request=httpx.Request("POST", "https://api.together.xyz/v1/chat/completions"))
    error = together.RateLimitError("rate limited", response=response, body=None)

    def raise_rate_limit(client, model_name, row, pricing):
        raise error

    monkeypatch.setattr(llm_pipeline, "process_row", raise_rate_limit)

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

    monkeypatch.setattr(llm_pipeline, "process_row", raise_value_error)

    result = run_row_safe(client=None, model_name="m", row=ROW, pricing={})

    assert result["pubid"] == 123
    assert result["status"] == "error"
    assert result["error_type"] == "other"
    assert result["error_message"] == "boom"
    assert result["cost_usd"] == 0.0
