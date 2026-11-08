from call_llm_concurrent import build_prompt


def test_build_prompt_includes_question_and_labeled_sections():
    context = {
        "labels": ["BACKGROUND", "RESULTS"],
        "contexts": ["Some background text.", "Some results text."],
    }
    prompt = build_prompt("Is X true?", context)

    assert "Is X true?" in prompt
    assert "[BACKGROUND] Some background text." in prompt
    assert "[RESULTS] Some results text." in prompt
