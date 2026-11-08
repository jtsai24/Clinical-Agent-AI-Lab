"""Look up a model's per-token price from Together's model catalog.

Together's own SDK client.models.list() requires a project_id this account
doesn't have set, so this hits the REST endpoint directly instead.
"""

import json
import urllib.request

MODELS_URL = "https://api.together.xyz/v1/models"


def get_model_pricing(model_id: str, api_key: str) -> dict:
    """Return {"input": price_per_1m_tokens, "output": price_per_1m_tokens} for model_id.

    Raises KeyError if model_id isn't in the catalog.
    """
    req = urllib.request.Request(
        MODELS_URL,
        headers={"Authorization": f"Bearer {api_key}", "User-Agent": "clinical-agent-ai-lab/1.0"},
    )
    with urllib.request.urlopen(req) as resp:
        models = json.loads(resp.read())

    for m in models:
        if m["id"] == model_id:
            pricing = m["pricing"]
            return {"input": pricing["input"], "output": pricing["output"]}

    raise KeyError(f"{model_id} not found in Together's model catalog")
