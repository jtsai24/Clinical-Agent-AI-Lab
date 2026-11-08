from cost import compute_cost


def test_compute_cost_combines_input_and_output_pricing():
    pricing = {"input": 0.15, "output": 0.5}
    cost = compute_cost(prompt_tokens=1_000_000, completion_tokens=1_000_000, pricing=pricing)
    assert cost == 0.65


def test_compute_cost_zero_tokens_is_zero_cost():
    pricing = {"input": 0.15, "output": 0.5}
    assert compute_cost(prompt_tokens=0, completion_tokens=0, pricing=pricing) == 0
