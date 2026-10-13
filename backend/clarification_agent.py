import re


class ClarificationAgent:
    def __init__(self):
        self.ambiguous_phrases = [
            "tell me about it",
            "what about it",
            "explain it",
            "what is this",
            "tell me more",
            "what do you mean",
            "how does it work",
            "what is that",
            "what about this",
        ]

        self.contextual_pronouns = [
            "it",
            "this",
            "that",
            "these",
            "those",
            "they",
            "them",
            "he",
            "she",
        ]

    def _normalize(self, query):
        return (query or "").strip()

    def _is_ambiguous(self, query_lower):
        cleaned = re.sub(r"[^a-z0-9\s]", " ", query_lower).strip()
        
        standalone_ambiguous = {
            "tell me about it",
            "what about it",
            "explain it",
            "what is this",
            "tell me more",
            "what do you mean",
            "how does it work",
            "what is that",
            "what about this",
            "tell me more about it",
            "tell me about this",
            "explain this",
            "how do i do it",
        }
        if cleaned in standalone_ambiguous:
            return True

        for phrase in self.ambiguous_phrases:
            if cleaned == phrase or cleaned == f"{phrase} please":
                return True

        return False

    def _is_incomplete(self, query_lower):
        short_query = re.sub(
            r"[^a-z0-9\s]",
            " ",
            query_lower
        ).strip()

        words = short_query.split()

        if len(words) <= 1:
            return True

        return False

    def _contains_context_dependency(self, query_lower):
        cleaned = re.sub(r"[^a-z0-9\s]", " ", query_lower).strip()
        words = cleaned.split()
        
        # Only flag if pronoun is the sole target (e.g., 'explain it', 'what is that')
        if len(words) <= 4:
            for pronoun in self.contextual_pronouns:
                if pronoun in words:
                    return True

        return False

    def _has_multi_part_query(self, query_lower):
        comparative_markers = [
            "difference between",
            "compare",
            "distinguish between",
            "versus",
            "vs",
            "relationship between",
            "differ from",
        ]
        if any(cm in query_lower for cm in comparative_markers):
            return False

        if query_lower.count("?") > 1:
            return True

        compound_markers = [
            " and also ",
            " as well as ",
            " additionally ",
        ]
        for marker in compound_markers:
            if marker in query_lower and query_lower.count(" ") > 7:
                return True

        return False

    def evaluate_query(self, query):
        normalized = self._normalize(query)

        if not normalized:
            return {
                "requires_clarification": True,
                "original_query": "",
                "clarification_question": "Please provide the question you want answered.",
                "reason": "Empty query.",
                "status": "clarification_required",
            }

        query_lower = normalized.lower()

        if self._is_ambiguous(query_lower):
            return {
                "requires_clarification": True,
                "original_query": normalized,
                "clarification_question": "Could you specify which topic or concept you want to know about?",
                "reason": "The query is vague and does not identify a specific topic.",
                "status": "clarification_required",
            }

        if self._is_incomplete(query_lower):
            return {
                "requires_clarification": True,
                "original_query": normalized,
                "clarification_question": "Could you provide the missing detail or subject you want information about?",
                "reason": "The query is too incomplete to identify the subject or intent.",
                "status": "clarification_required",
            }

        if self._contains_context_dependency(query_lower):
            return {
                "requires_clarification": True,
                "original_query": normalized,
                "clarification_question": "Could you clarify what 'it' or the earlier reference refers to?",
                "reason": "The query relies on missing context from a previous turn or an unclear reference.",
                "status": "clarification_required",
            }

        if self._has_multi_part_query(query_lower):
            return {
                "requires_clarification": True,
                "original_query": normalized,
                "clarification_question": "Could you clarify which part of the question you want answered first or whether you want a combined answer?",
                "reason": "The query contains several possible interpretations or mixed requests.",
                "status": "clarification_required",
            }

        return {
            "requires_clarification": False,
            "original_query": normalized,
            "clarification_question": "",
            "reason": "The query is clear enough to process.",
            "status": "clear",
        }

    def refine_query(self, original_query, clarification_response):
        original = (original_query or "").strip()
        clarification = (clarification_response or "").strip()

        if not original:
            return clarification

        if not clarification:
            return original

        lower_original = original.lower().strip()
        lower_response = clarification.lower().strip()

        combined_phrases = [
            "combined answer",
            "both parts",
            "both questions",
            "all parts",
            "answer both",
            "covering both",
            "cover both",
            "all of them",
        ]

        if any(
            phrase in lower_response
            for phrase in combined_phrases
        ):
            return original

        if any(
            pattern in lower_original
            for pattern in [
                "tell me about it",
                "what is this",
                "what about it",
                "what is that",
                "explain it",
            ]
        ):
            return f"What is {clarification}?"

        if "how does it work" in lower_original:
            return f"How does {clarification} work?"

        if "why is it used" in lower_original:
            return f"Why is {clarification} used?"

        if "who is it" in lower_original:
            return f"Who is {clarification}?"

        return f"{original} {clarification}".strip()