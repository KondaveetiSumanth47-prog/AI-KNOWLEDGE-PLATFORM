import re

from clarification_agent import ClarificationAgent
from conversation_memory_agent import ConversationMemoryAgent
from query_understanding_agent import QueryUnderstandingAgent
from retrieval_agent import RetrievalAgent
from response_generation_agent import ResponseGenerationAgent
from analytics_service import analytics_service


class Orchestrator:

    def __init__(self, top_k=3, distance_threshold=0.60):
        self.query_agent = QueryUnderstandingAgent()

        self.retrieval_agent = RetrievalAgent(
            top_k=top_k,
            distance_threshold=distance_threshold
        )

        self.response_agent = ResponseGenerationAgent()
        self.clarification_agent = ClarificationAgent()

        self.memory_store = {}

    def _get_memory(self, session_id):
        session_key = session_id or "default-session"

        if session_key not in self.memory_store:
            self.memory_store[session_key] = ConversationMemoryAgent(
                session_id=session_key
            )

        return self.memory_store[session_key]

    def _resolve_memory_reference(self, query, memory_context):
        if not isinstance(query, str):
            return query

        if not isinstance(memory_context, dict):
            return query

        memory_topic = memory_context.get("topic")

        if not memory_topic or memory_topic == "general":
            return query

        query_text = query.strip()
        query_lower = query_text.lower()

        topic_text = str(memory_topic).strip()
        topic_lower = topic_text.lower()

        if "what are the types of it" in query_lower:
            return query_lower.replace(
                "what are the types of it",
                f"what are the types of {topic_lower}"
            ).capitalize()

        if "what are its types" in query_lower:
            return query_lower.replace(
                "what are its types",
                f"what are the types of {topic_lower}"
            ).capitalize()

        if "what is it" in query_lower:
            return query_lower.replace(
                "what is it",
                f"what is {topic_lower}"
            ).capitalize()

        if "what is its use" in query_lower:
            return query_lower.replace(
                "what is its use",
                f"what is the use of {topic_lower}"
            ).capitalize()

        if "why is it used" in query_lower:
            return query_lower.replace(
                "why is it used",
                f"why is {topic_lower} used"
            ).capitalize()

        if "how does it work" in query_lower:
            return query_lower.replace(
                "how does it work",
                f"how does {topic_lower} work"
            ).capitalize()

        if "how does this work" in query_lower:
            return query_lower.replace(
                "how does this work",
                f"how does {topic_lower} work"
            ).capitalize()

        if "how does that work" in query_lower:
            return query_lower.replace(
                "how does that work",
                f"how does {topic_lower} work"
            ).capitalize()

        if "explain it" in query_lower:
            return query_lower.replace(
                "explain it",
                f"explain {topic_lower}"
            ).capitalize()

        if "explain this" in query_lower:
            return query_lower.replace(
                "explain this",
                f"explain {topic_lower}"
            ).capitalize()

        if "tell me more" in query_lower:
            return f"Tell me more about {topic_text}"

        if "what about it" in query_lower:
            return query_lower.replace(
                "what about it",
                f"what about {topic_lower}"
            ).capitalize()

        pronoun_patterns = [
            r"\bit\b",
            r"\bthis\b",
            r"\bthat\b",
            r"\bthey\b",
            r"\bthem\b",
        ]

        for pattern in pronoun_patterns:
            if re.search(pattern, query_lower):
                return re.sub(
                    pattern,
                    topic_text,
                    query_text,
                    count=1,
                    flags=re.IGNORECASE
                )

        return query

    def _record_analytics(
        self,
        query,
        session_id,
        query_type="unknown",
        status="unknown",
        confidence=None,
        retrieved_results=None,
        sources=None,
        clarification_required=False,
        routing="unknown",
        domain="unknown"
    ):
        try:
            analytics_service.record_query(
                query=query,
                query_type=query_type,
                status=status,
                confidence=confidence or {
                    "label": "Unknown",
                    "score": 0.0
                },
                retrieved_results=retrieved_results or [],
                sources=sources or [],
                clarification_required=clarification_required,
                session_id=session_id,
                domain=domain,
                routing=routing
            )
        except Exception as exc:
            print(f"[WARN] Analytics recording failed: {exc}")

    def _infer_domain(self, sources):
        if not sources:
            return "unknown"

        if isinstance(sources, list):
            valid_sources = [
                str(source).strip()
                for source in sources
                if source
            ]

            if valid_sources:
                return valid_sources[0]

        return "unknown"

    def process_query(
        self,
        query,
        session_id="default-session",
        original_query=None,
        clarification_response=None,
        top_k=None,
        domain=None
    ):
        effective_top_k = self.retrieval_agent.top_k

        if top_k is not None:
            try:
                requested_top_k = int(top_k)
            except (TypeError, ValueError):
                requested_top_k = 3

            if requested_top_k not in {1, 3, 5}:
                requested_top_k = 3

            effective_top_k = requested_top_k
            self.retrieval_agent.top_k = effective_top_k

        if not isinstance(query, str) or not query.strip():

            if clarification_response and original_query:
                query = self.clarification_agent.refine_query(
                    original_query,
                    clarification_response
                )

            else:
                response = {
                    "query": "",
                    "query_type": "ambiguous",
                    "classification_confidence": 0.0,
                    "answer": "Please provide a valid question.",
                    "sources": [],
                    "confidence": {
                        "label": "Low",
                        "score": 0.0
                    },
                    "retrieved_chunks": [],
                    "top_k": effective_top_k,
                    "status": "invalid_query",
                    "routing": "clarification"
                }

                self._record_analytics(
                    query="",
                    session_id=session_id,
                    query_type="ambiguous",
                    status="invalid_query",
                    confidence=response["confidence"],
                    retrieved_results=[],
                    sources=[],
                    clarification_required=True,
                    routing="clarification",
                    domain=domain or "unknown"
                )

                return response

        memory = self._get_memory(session_id)

        memory_context = memory.get_relevant_context(query)

        resolved_query = self._resolve_memory_reference(
            query,
            memory_context
        )

        target_query = (
            resolved_query
            if resolved_query.strip()
            else query
        )

        clarification_was_provided = (
            bool(original_query)
            and bool(clarification_response)
        )

        if clarification_was_provided:

            target_query = self.clarification_agent.refine_query(
                original_query,
                clarification_response
            )

            memory.add_exchange(
                original_query,
                "Clarification provided.",
                topic=memory_context.get(
                    "topic",
                    "clarification"
                ),
                sources=[],
                clarification=clarification_response,
                refined_query=target_query
            )

            query_for_classification = target_query

        else:
            query_for_classification = target_query

        if clarification_was_provided:

            clarification_result = {
                "requires_clarification": False,
                "original_query": original_query,
                "clarification_question": "",
                "reason": (
                    "Clarification provided. "
                    "Proceeding with the refined query."
                ),
                "status": "clarification_resolved"
            }

        else:

            clarification_result = (
                self.clarification_agent.evaluate_query(
                    query_for_classification
                )
            )

            if clarification_result.get(
                "requires_clarification"
            ):

                response = {
                    "question": query_for_classification,
                    "query": query_for_classification,
                    "query_type": "ambiguous",
                    "classification_confidence": 0.0,
                    "answer": "",
                    "sources": [],
                    "confidence": {
                        "label": "Low",
                        "score": 0.0
                    },
                    "retrieved_chunks": [],
                    "top_k": effective_top_k,
                    "clarification": clarification_result,
                    "conversation_context": memory_context,
                    "status": "clarification_required",
                    "routing": "clarification"
                }

                self._record_analytics(
                    query=query_for_classification,
                    session_id=session_id,
                    query_type="ambiguous",
                    status="clarification_required",
                    confidence=response["confidence"],
                    retrieved_results=[],
                    sources=[],
                    clarification_required=True,
                    routing="clarification",
                    domain=domain or "unknown"
                )

                return response

        classification = self.query_agent.classify_query(
            query_for_classification
        )

        if not isinstance(classification, dict):

            response = {
                "question": query_for_classification,
                "query": query_for_classification,
                "query_type": "ambiguous",
                "classification_confidence": 0.0,
                "answer": (
                    "The query could not be classified. "
                    "Please try a clearer question."
                ),
                "sources": [],
                "confidence": {
                    "label": "Low",
                    "score": 0.0
                },
                "retrieved_chunks": [],
                "top_k": effective_top_k,
                "clarification": clarification_result,
                "conversation_context": memory_context,
                "status": "classification_failed",
                "routing": "clarification"
            }

            self._record_analytics(
                query=query_for_classification,
                session_id=session_id,
                query_type="ambiguous",
                status="classification_failed",
                confidence=response["confidence"],
                retrieved_results=[],
                sources=[],
                clarification_required=True,
                routing="clarification",
                domain=domain or "unknown"
            )

            return response

        if classification.get("query_type") == "ambiguous":

            response = {
                "question": query_for_classification,
                "query": query_for_classification,
                "query_type": "ambiguous",
                "classification_confidence": classification.get(
                    "classification_confidence",
                    0.0
                ),
                "answer": (
                    "Your question is ambiguous. "
                    "Please clarify what you want to know."
                ),
                "sources": [],
                "confidence": {
                    "label": "Low",
                    "score": 0.0
                },
                "retrieved_chunks": [],
                "top_k": effective_top_k,
                "clarification": clarification_result,
                "conversation_context": memory_context,
                "status": "clarification_required",
                "routing": "clarification"
            }

            self._record_analytics(
                query=query_for_classification,
                session_id=session_id,
                query_type="ambiguous",
                status="clarification_required",
                confidence=response["confidence"],
                retrieved_results=[],
                sources=[],
                clarification_required=True,
                routing="clarification",
                domain=domain or "unknown"
            )

            return response

        retrieval_result = self.retrieval_agent.retrieve(
            query_for_classification,
            classification
        )

        retrieved_chunks = retrieval_result.get(
            "results",
            []
        )

        if (
            retrieval_result.get("status")
            == "no_relevant_information"
            or not retrieved_chunks
        ):

            response = {
                "question": query_for_classification,
                "query": query_for_classification,
                "query_type": classification.get(
                    "query_type",
                    "unknown"
                ),
                "classification_confidence": classification.get(
                    "classification_confidence",
                    0.0
                ),
                "answer": (
                    "I could not find sufficient information "
                    "in the current knowledge base to answer "
                    "this question."
                ),
                "sources": [],
                "confidence": {
                    "label": "Low",
                    "score": 0.0
                },
                "retrieved_chunks": [],
                "top_k": effective_top_k,
                "clarification": clarification_result,
                "conversation_context": memory_context,
                "status": "no_relevant_information",
                "routing": classification.get(
                    "routing",
                    "retrieval"
                )
            }

            memory.add_exchange(
                query_for_classification,
                response["answer"],
                topic=memory_context.get(
                    "topic",
                    "general"
                ),
                sources=[],
                refined_query=query_for_classification
            )

            self._record_analytics(
                query=query_for_classification,
                session_id=session_id,
                query_type=response["query_type"],
                status=response["status"],
                confidence=response["confidence"],
                retrieved_results=[],
                sources=[],
                clarification_required=clarification_was_provided,
                routing=response["routing"],
                domain=domain or "unknown"
            )

            return response

        response_result = self.response_agent.generate_response(
            query_for_classification,
            retrieved_chunks,
            classification.get(
                "query_type",
                "factual"
            )
        )

        final_response = {
            "question": query_for_classification,
            "query": query_for_classification,
            "refined_query": query_for_classification,
            "query_type": classification.get(
                "query_type",
                "unknown"
            ),
            "classification_confidence": classification.get(
                "classification_confidence",
                0.0
            ),
            "answer": response_result.get(
                "answer",
                "I could not generate an answer."
            ),
            "sources": response_result.get(
                "sources",
                []
            ),
            "confidence": response_result.get(
                "confidence",
                {
                    "label": "Low",
                    "score": 0.0
                }
            ),
            "retrieved_chunks": retrieved_chunks,
            "top_k": effective_top_k,
            "clarification": clarification_result,
            "conversation_context": memory_context,
            "status": response_result.get(
                "status",
                "success"
            ),
            "routing": classification.get(
                "routing",
                "retrieval"
            )
        }

        memory.add_exchange(
            query_for_classification,
            final_response["answer"],
            topic=(
                memory_context.get("topic")
                if memory_context.get("topic") != "general"
                else None
            ),
            sources=final_response["sources"],
            refined_query=query_for_classification
        )

        analytics_domain = (
            domain
            or self._infer_domain(
                final_response["sources"]
            )
        )

        self._record_analytics(
            query=query_for_classification,
            session_id=session_id,
            query_type=final_response["query_type"],
            status=final_response["status"],
            confidence=final_response["confidence"],
            retrieved_results=retrieved_chunks,
            sources=final_response["sources"],
            clarification_required=clarification_was_provided,
            routing=final_response["routing"],
            domain=analytics_domain
        )

        return final_response