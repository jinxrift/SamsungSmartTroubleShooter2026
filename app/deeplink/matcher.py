"""Match troubleshooting actions to the local Samsung deeplink catalog."""

import json
import re
from pathlib import Path
from typing import Optional


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "change", "check",
    "click", "configure", "device", "disable", "do", "enable", "for", "from",
    "go", "help", "how", "in", "into", "is", "it", "manage", "modify", "of",
    "off", "on", "open", "or", "page", "phone", "please", "select", "set",
    "settings", "screen", "switch", "tap", "the", "this", "to", "turn", "update",
    "use", "view", "with", "your",
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def _contains_phrase(text_tokens: list[str], phrase_tokens: list[str]) -> bool:
    size = len(phrase_tokens)
    return bool(size) and any(
        text_tokens[index:index + size] == phrase_tokens
        for index in range(len(text_tokens) - size + 1)
    )


class DeeplinkMatcher:
    def __init__(self, deeplink_file: str):
        with open(Path(deeplink_file), "r", encoding="utf-8") as file:
            data = json.load(file)
        self.entries = [
            entry
            for entry in data.get("deeplinks", [])
            if isinstance(entry, dict) and entry.get("deeplink")
        ]
        self.by_key: dict[str, list[dict]] = {}
        for entry in self.entries:
            key = (entry.get("validation") or {}).get("key")
            if isinstance(key, str) and key.strip():
                self.by_key.setdefault(" ".join(_tokens(key)), []).append(entry)

    @staticmethod
    def _detect_intent(action_name: str, steps: list[str]) -> str:
        text = " ".join(_tokens(f"{action_name} {' '.join(steps)}"))
        if re.search(r"\b(disable|turn off|switch off|deactivate)\b", text):
            return "off"
        if re.search(r"\b(enable|turn on|switch on|activate)\b", text):
            return "on"
        if re.search(r"\b(increase|decrease|adjust|change|modify|set|update)\b", text):
            return "update"
        if re.search(r"\b(open|view|access|navigate)\b", text):
            return "click"
        return "unknown"

    @staticmethod
    def _intent_score(entry: dict, intent: str) -> float:
        expected_type = {
            "on": "onURL",
            "off": "offURL",
            "update": "updateURL",
            "click": "onClickURL",
        }.get(intent)
        original_type = entry.get("originalType")
        if original_type == expected_type:
            return 0.24
        if intent in {"on", "off"} and original_type in {"onURL", "offURL"}:
            return -0.30
        if intent in {"on", "off", "update"} and original_type == "onClickURL":
            return -0.12
        return 0.0

    def match_step_group(
        self,
        action_name: str,
        description: str,
        steps: list[str],
        threshold: float = 0.42,
    ) -> Optional[dict]:
        full_tokens = _tokens(f"{action_name} {' '.join(steps)} {description}")
        setting_tokens = [token for token in full_tokens if token not in _STOP_WORDS]
        if not setting_tokens:
            return None

        intent = self._detect_intent(action_name, steps)
        candidates = []
        for key, entries in self.by_key.items():
            key_tokens = key.split()
            overlap = len(set(key_tokens) & set(setting_tokens))
            coverage = overlap / len(key_tokens)
            precision = overlap / len(set(setting_tokens))
            exact_phrase = _contains_phrase(full_tokens, key_tokens)
            phrase_score = 0.68 + min(len(key_tokens), 5) * 0.025 if exact_phrase else 0.0

            for entry in entries:
                metadata_tokens = set(
                    _tokens(" ".join(
                        str(entry.get(field) or "")
                        for field in ("message", "description", "qna_description")
                    ))
                )
                metadata_overlap = len(set(setting_tokens) & metadata_tokens) / max(
                    len(set(setting_tokens)), 1
                )
                score = (
                    phrase_score
                    + coverage * 0.30
                    + precision * 0.12
                    + metadata_overlap * 0.08
                    + self._intent_score(entry, intent)
                )
                candidates.append((score, coverage, len(key_tokens), entry))

        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        best_score, coverage, _, entry = candidates[0]
        if best_score < threshold or coverage < 0.5:
            return None
        return entry

    def build_step_group_result(
        self,
        action_name: str,
        description: str,
        steps: list[str],
        threshold: float = 0.42,
    ) -> dict:
        match = self.match_step_group(action_name, description, steps, threshold)
        if match is None:
            return {"actionableDeeplink": None, "validationDeeplink": None}

        actionable = {
            key: match.get(key)
            for key in ("deeplink", "description", "message", "classes", "originalType")
        }
        validation = match.get("validation") or {}
        validation_result = None
        if validation.get("deeplink") and validation.get("key"):
            validation_result = {
                key: validation.get(key)
                for key in ("deeplink", "key", "resultType", "condition", "value")
            }
        return {
            "actionableDeeplink": actionable,
            "validationDeeplink": validation_result,
        }