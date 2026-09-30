"""Convert supplied SIIS text into schema-compatible troubleshooting goals."""

import re

from app.models.schema import Goal
from app.services.llm_engine import extract_with_llm


_NUMBERED_SECTION = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:step\s+)?(\d+)[.:)]\s*(.*?)\s*$"
    r"(.*?)(?=^\s*(?:#{1,6}\s*)?(?:step\s+)?\d+[.:)]\s*|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_HEADING = re.compile(
    r"^\s*#{1,6}\s+(.+?)\s*$\n?(.*?)(?=^\s*#{1,6}\s+.+?$|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _clean_title(value: str) -> str:
    value = re.sub(r"^\s*(?:step\s+)?\d+[.:)]\s*", "", value, flags=re.I)
    value = re.sub(r"[*_`#]", "", value)
    return re.sub(r"\s+", " ", value).strip(" \t:-")


def _clean_steps(text: str) -> list[str]:
    steps = []
    for line in text.splitlines():
        step = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line).strip()
        step = re.sub(r"[*_`]", "", step).strip()
        if step and step not in {"\"\"", "'''"}:
            steps.append(step)
    return steps


def _sections(content: str) -> list[tuple[str, str]]:
    numbered = []
    for match in _NUMBERED_SECTION.finditer(content):
        title = _clean_title(match.group(2))
        if title:
            numbered.append((title, match.group(3)))
    if numbered:
        return numbered

    sections = []
    for match in _HEADING.finditer(content):
        title = _clean_title(match.group(1))
        if title and not title.casefold().startswith(("troubleshooting ", "how to ")):
            sections.append((title, match.group(2)))
    if sections:
        return sections

    text = content.strip()
    if not text:
        return []
    first_line, separator, remainder = text.partition("\n")
    title = _clean_title(first_line)
    steps = remainder if separator else text
    if not title or title.casefold() == steps.casefold():
        title = "Troubleshooting steps"
    return [(title, steps)]


def _category(action_name: str, steps: list[str]) -> str:
    text = f"{action_name} {' '.join(steps)}".casefold()
    if re.search(r"\b(factory reset|erase|wipe|liquid damage|physical damage|repair|service center)\b", text):
        return "critical"
    return "manual"


def _description(action_name: str) -> str:
    verb = action_name.split(maxsplit=1)[0].casefold() if action_name else ""
    descriptions = {
        "check": "It will help you check device issues",
        "verify": "It will help you verify device connections",
        "restart": "It will help you restart your device safely",
        "clear": "It will help clear temporary app data",
        "update": "It will help you update device software",
        "contact": "It will help you contact support",
    }
    return descriptions.get(verb, "It will help you troubleshoot this issue")


def parse_siis_actions(content: str) -> list[dict]:
    """Parse action titles and steps without adding instructions to SIIS text."""
    actions = []
    for title, body in _sections(content):
        steps = _clean_steps(body)
        if not steps:
            continue
        actions.append(
            {
                "actionName": title,
                "description": _description(title),
                "steps": steps,
                "category": _category(title, steps),
            }
        )
    return actions


def process_siis(query, siis_response):
    extracted = extract_with_llm(
        query,
        siis_response.title,
        siis_response.content,
    )
    actions = [
        {
            "actionName": item["actionName"],
            "description": item["description"],
            "stepGroups": [
                {
                    "steps": item["steps"],
                    "actionableDeeplink": None,
                    "validationDeeplink": None,
                }
            ],
            "category": item["category"],
        }
        for item in extracted["actions"]
    ]
    goal = {
        "goal": f"Follow these steps to troubleshoot {siis_response.title}",
        "title": siis_response.title,
        "actions": actions,
        "score": 0.95,
    }
    Goal(**goal)
    return {"goals": [goal]}