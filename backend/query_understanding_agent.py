import re


class QueryUnderstandingAgent:

    def classify_query(self, query):
        query = query.strip()

        if not query:
            return {
                "query": query,
                "query_type": "ambiguous",
                "classification_confidence": 0.0,
                "routing": "clarification"
            }

        query_lower = query.lower()

        # Ambiguous queries
        ambiguous_patterns = [
            r"^tell me about it[\s?!.]*$",
            r"^what about it[\s?!.]*$",
            r"^explain it[\s?!.]*$",
            r"^what is this[\s?!.]*$",
            r"^what is that[\s?!.]*$",
            r"^what about this[\s?!.]*$",
            r"^tell me more[\s?!.]*$",
            r"^what do you mean[\s?!.]*$",
            r"^how does it work[\s?!.]*$"
        ]

        for pattern in ambiguous_patterns:
            if re.search(pattern, query_lower):
                return {
                    "query": query,
                    "query_type": "ambiguous",
                    "classification_confidence": 0.90,
                    "routing": "clarification"
                }

        # Comparative queries
        comparative_words = [
            "difference",
            "compare",
            "comparison",
            "different from",
            "better than",
            "versus",
            " vs ",
            "advantages and disadvantages"
        ]

        if any(word in query_lower for word in comparative_words):
            return {
                "query": query,
                "query_type": "comparative",
                "classification_confidence": 0.90,
                "routing": "retrieval"
            }

        # Procedural queries
        procedural_words = [
            "how",
            "steps",
            "process",
            "procedure",
            "method",
            "ways",
            "how does",
            "how to"
        ]

        if any(word in query_lower for word in procedural_words):
            return {
                "query": query,
                "query_type": "procedural",
                "classification_confidence": 0.88,
                "routing": "retrieval"
            }

        # Factual queries
        factual_words = [
            "what",
            "who",
            "where",
            "when",
            "which",
            "define",
            "meaning",
            "is",
            "are"
        ]

        if any(word in query_lower for word in factual_words):
            return {
                "query": query,
                "query_type": "factual",
                "classification_confidence": 0.85,
                "routing": "retrieval"
            }

        # Default case
        return {
            "query": query,
            "query_type": "factual",
            "classification_confidence": 0.70,
            "routing": "retrieval"
        }