from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from app.deeplink.matcher import DeeplinkMatcher


@lru_cache(maxsize=1)
def _matcher() -> DeeplinkMatcher:
    catalog = Path(__file__).resolve().parents[2] / "data" / "deeplinks.json"
    return DeeplinkMatcher(str(catalog))


def match_deeplinks(troubleshooting: dict) -> dict:
    result = deepcopy(troubleshooting)
    matcher = _matcher()
    for goal in result.get("goals", []):
        for action in goal.get("actions", []):
            has_automatic_action = False
            for step_group in action.get("stepGroups", []):
                matched = matcher.build_step_group_result(
                    action_name=action.get("actionName", ""),
                    description=action.get("description", ""),
                    steps=step_group.get("steps", []),
                )
                step_group.update(matched)
                deeplink = matched["actionableDeeplink"]
                if deeplink and deeplink.get("originalType") in {
                    "onURL", "offURL", "updateURL"
                }:
                    has_automatic_action = True
            if action.get("category") != "critical" and has_automatic_action:
                action["category"] = "auto"
    return result