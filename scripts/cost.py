"""Compute the dollar cost of one LLM call from its token usage and model pricing.

Pure function, no I/O.
"""


def compute_cost(prompt_tokens: int, completion_tokens: int, pricing: dict) -> float:
    """pricing is {"input": price_per_1m_tokens, "output": price_per_1m_tokens}."""
    return (prompt_tokens / 1_000_000) * pricing["input"] + (completion_tokens / 1_000_000) * pricing["output"]
