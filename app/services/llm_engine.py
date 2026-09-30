"""Optional structured LLM extraction with deterministic SIIS fallback."""

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen


def _is_grounded(action: dict, content: str) -> bool:
    action_name = action.get("actionName")
    description = action.get("description")
    steps = action.get("steps")
    category = action.get("category")
    return (
        isinstance(action_name, str)
        and bool(action_name.strip())
        and action_name.strip() in content
        and isinstance(description, str)
        and description.casefold().startswith("it will ")
        and 5 <= len(description.split()) <= 7
        and isinstance(steps, list)
        and bool(steps)
        and all(
            isinstance(step, str) and step.strip() and step.strip() in content
            for step in steps
        )
        and category in {"auto", "manual", "critical"}
    )


def _request_llm(query: str, title: str, content: str) -> list[dict] | None:
    endpoint = os.getenv("LLM_API_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if not endpoint or not api_key or not model:
        return None

    prompt = (
        "Extract troubleshooting actions from the supplied SIIS content. "
        "Return only JSON with an actions array; each action must contain "
        "actionName, description, steps, and category. Copy actionName and "
        "each step verbatim from the SIIS content. Do not invent instructions. "
        "Descriptions must start with 'It will' and contain 5 to 7 words. "
        "Categories are auto, manual, or critical.\n"
        f"Query: {query}\nSIIS title: {title}\nSIIS content:\n{content}"
    )
    request = Request(
        endpoint,
        data=json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        message = response_data["choices"][0]["message"]["content"]
        actions = json.loads(message).get("actions")
        if isinstance(actions, list) and actions and all(
            isinstance(action, dict) and _is_grounded(action, content)
            for action in actions
        ):
            return actions
    except (KeyError, IndexError, TypeError, ValueError, URLError, TimeoutError):
        return None
    return None


def extract_with_llm(query: str, title: str, content: str) -> dict:
    """Return validated actions, falling back to deterministic SIIS parsing."""
    actions = _request_llm(query, title, content)
    if actions is None:
        from app.services.siis_engine import parse_siis_actions

        actions = parse_siis_actions(content)
    return {"actions": actions}