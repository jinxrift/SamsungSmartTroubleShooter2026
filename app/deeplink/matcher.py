import json
import re

from pathlib import Path
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class DeeplinkMatcher:

    def __init__(self, deeplink_file: str):
        self.deeplink_file = Path(deeplink_file)

        with open(self.deeplink_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.entries = [
            entry
            for entry in data["deeplinks"]
            if isinstance(entry, dict) and "deeplink" in entry
        ]

        self.vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english", ngram_range=(1, 3)
        )

        # Build documents mainly from setting-specific information.
        self.documents = []

        for entry in self.entries:
            text = self._build_document(entry)
            self.documents.append(text)

        print("DOCUMENT COUNT:", len(self.documents))
        print("FIRST DOCUMENT:", repr(self.documents[0]) if self.documents else "EMPTY")

        self.matrix = self.vectorizer.fit_transform(self.documents)

    # ---------------------------------------------------------
    # TEXT HELPERS
    # ---------------------------------------------------------

    def _clean(self, text: str) -> str:
        if not text:
            return ""

        text = text.lower()

        # Normalize common punctuation
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Normalize repeated whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _tokens(self, text: str):
        return set(self._clean(text).split())

    def _build_document(self, entry: dict) -> str:

        description = entry.get("description") or ""
        message = entry.get("message") or ""
        qna = entry.get("qna_description") or ""

        validation = entry.get("validation") or {}
        validation_key = validation.get("key") or ""

        # Give important setting identifiers more representation
        # in the TF-IDF document.
        return " ".join(
            [
                validation_key,
                validation_key,
                validation_key,
                message,
                message,
                description,
                qna,
            ]
        )

    # ---------------------------------------------------------
    # INTENT DETECTION
    # ---------------------------------------------------------

    def _detect_intent(self, action_name: str, steps: list[str]) -> str:

        text = self._clean(action_name + " " + " ".join(steps))

        # Explicit state-changing actions first
        if re.search(r"\b(disable|turn off|switch off|deactivate|stop)\b", text):
            return "off"

        if re.search(r"\b(enable|turn on|switch on|activate|start)\b", text):
            return "on"

        if re.search(r"\b(increase|decrease|adjust|change|modify|set|update)\b", text):
            return "update"

        # Navigation is deliberately last.
        if re.search(r"\b(open|view|access|navigate)\b", text):
            return "click"

        return "unknown"

    # ---------------------------------------------------------
    # SETTING-SPECIFIC TERM EXTRACTION
    # ---------------------------------------------------------

    def _extract_setting_terms(self, action_name: str, steps: list[str]):

        text = self._clean(action_name + " " + " ".join(steps))

        # Words that describe navigation rather than the setting.
        navigation_words = {
            "navigate",
            "open",
            "tap",
            "click",
            "select",
            "go",
            "settings",
            "menu",
            "page",
            "screen",
            "device",
            "phone",
            "tablet",
            "option",
            "options",
            "choose",
            "access",
        }

        # Very generic words that should not drive matching.
        generic_words = {
            "the",
            "a",
            "an",
            "to",
            "and",
            "for",
            "your",
            "on",
            "off",
            "this",
            "that",
            "data",
            "use",
            "using",
            "will",
            "can",
            "with",
            "from",
            "change",
            "adjust",
            "modify",
            "manage",
            "configure",
            "customize",
            "set",
        }

        tokens = self._tokens(text)

        return tokens - navigation_words - generic_words

    # ---------------------------------------------------------
    # ACTION TYPE COMPATIBILITY
    # ---------------------------------------------------------

    def _type_score(self, entry: dict, intent: str) -> float:

        original_type = entry.get("originalType")

        if not original_type:
            return 0.0

        if intent == "off":

            if original_type == "offURL":
                return 0.30

            if original_type == "onURL":
                return -0.30

        elif intent == "on":

            if original_type == "onURL":
                return 0.30

            if original_type == "offURL":
                return -0.30

        elif intent == "update":

            if original_type == "updateURL":
                return 0.25

        elif intent == "click":

            if original_type == "onClickURL":
                return 0.05

        return 0.0

    # ---------------------------------------------------------
    # MATCHING
    # ---------------------------------------------------------

    def match_step_group(
        self,
        action_name: str,
        description: str,
        steps: list[str],
        threshold: float = 0.30,
    ) -> Optional[dict]:

        intent = self._detect_intent(action_name, steps)

        # -----------------------------------------------------
        # 1. TF-IDF semantic similarity
        # -----------------------------------------------------

        query_text = " ".join(
            [
                action_name,
                action_name,
                action_name,
                " ".join(steps),
                " ".join(steps),
                description,
            ]
        )

        query_vector = self.vectorizer.transform([query_text])

        semantic_scores = cosine_similarity(query_vector, self.matrix)[0]

        # -----------------------------------------------------
        # 2. Exact token overlap
        # -----------------------------------------------------

        setting_terms = self._extract_setting_terms(action_name, steps)
        if not setting_terms:
            return None

        candidates = []

        for index, entry in enumerate(self.entries):

            validation = entry.get("validation") or {}

            validation_key = validation.get("key") or ""
            message = entry.get("message") or ""
            entry_description = entry.get("description") or ""

            validation_tokens = self._tokens(validation_key)
            message_tokens = self._tokens(message)
            description_tokens = self._tokens(entry_description)

            # Strongest signal:
            # action/step setting terms vs validation key
            validation_overlap = len(setting_terms & validation_tokens) / max(
                len(setting_terms), 1
            )

            message_overlap = len(setting_terms & message_tokens) / max(
                len(setting_terms), 1
            )

            description_overlap = len(setting_terms & description_tokens) / max(
                len(setting_terms), 1
            )

            semantic = semantic_scores[index]

            type_bonus = self._type_score(entry, intent)

            # -------------------------------------------------
            # Final score
            # -------------------------------------------------

            final_score = (
                semantic * 0.30
                + validation_overlap * 0.45
                + message_overlap * 0.15
                + description_overlap * 0.10
                + type_bonus
            )

            candidates.append(
                (
                    final_score,
                    index,
                    semantic,
                    validation_overlap,
                    message_overlap,
                    description_overlap,
                    type_bonus,
                )
            )

        candidates.sort(key=lambda x: x[0], reverse=True)
        print("\nTOP 10 CANDIDATES:")
        for candidate in candidates[:10]:
            (
                score,
                index,
                semantic,
                validation_overlap,
                message_overlap,
                description_overlap,
                type_bonus,
            ) = candidate
            print(
                round(score, 4),
                "| semantic:",
                round(semantic, 4),
                "| validation:",
                round(validation_overlap, 4),
                "| message:",
                round(message_overlap, 4),
                "| description:",
                round(description_overlap, 4),
                "| type:",
                round(type_bonus, 4),
                "|",
                self.entries[index].get("message"),
                "| key:",
                (self.entries[index].get("validation") or {}).get("key"),
            )

        best = candidates[0]

        if best[0] < threshold:
            return None

        return self.entries[best[1]]

    # ---------------------------------------------------------
    # OUTPUT BUILDER
    # ---------------------------------------------------------

    def build_step_group_result(
        self,
        action_name: str,
        description: str,
        steps: list[str],
        threshold: float = 0.30,
    ):

        match = self.match_step_group(action_name, description, steps, threshold)

        if match is None:
            return {"actionableDeeplink": None, "validationDeeplink": None}

        validation = match.get("validation")

        actionable = {
            "deeplink": match.get("deeplink"),
            "description": match.get("description"),
            "message": match.get("message"),
            "classes": match.get("classes"),
            "originalType": match.get("originalType"),
        }

        validation_result = None

        if validation:
            validation_result = {
                "deeplink": validation.get("deeplink"),
                "key": validation.get("key"),
                "resultType": validation.get("resultType"),
                "condition": validation.get("condition"),
                "value": validation.get("value"),
            }

        return {
            "actionableDeeplink": actionable,
            "validationDeeplink": validation_result,
        }
