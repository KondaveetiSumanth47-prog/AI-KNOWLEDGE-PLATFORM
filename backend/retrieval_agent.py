import re
from embeddings import create_embeddings
from vector_store import search_chunks


class RetrievalAgent:

    def __init__(self, top_k=3, distance_threshold=0.60, min_relevance_score=0.40):
        self.top_k = top_k
        self.distance_threshold = distance_threshold
        self.min_relevance_score = min_relevance_score

    def _extract_keywords(self, query):
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "what", "how", "why",
            "which", "who", "when", "where", "does", "do", "did", "can", "could",
            "would", "should", "of", "in", "to", "for", "with", "on", "at", "from",
            "by", "about", "it", "this", "that", "these", "those"
        }
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]+\b", query.lower())
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    def retrieve(self, query, query_classification=None):
        if not isinstance(query, str) or not query.strip():
            return {
                "query": "",
                "query_type": "unknown",
                "top_k": self.top_k,
                "results": [],
                "result_count": 0,
                "status": "no_relevant_information",
            }

        cleaned_query = query.strip()
        query_type = (
            query_classification.get("query_type", "factual")
            if isinstance(query_classification, dict)
            else "factual"
        )

        query_embedding = create_embeddings([cleaned_query])[0]

        # Retrieve a broader candidate pool to enable deduplication and diverse ranking
        candidate_k = max(self.top_k * 4, 12)
        results = search_chunks(
            query_embedding,
            top_k=candidate_k
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        keywords = self._extract_keywords(cleaned_query)

        candidates = []
        seen_texts = set()

        for i, document in enumerate(documents):
            doc_text = (document or "").strip()
            if not doc_text:
                continue

            # Duplicate-content detection: deduplicate identical chunks from different files
            norm_doc = " ".join(doc_text.lower().split())
            if norm_doc in seen_texts:
                continue
            seen_texts.add(norm_doc)

            raw_dist = float(distances[i]) if i < len(distances) and distances[i] is not None else 1.0
            base_score = max(0.0, min(1.0, 1.0 - raw_dist))

            # Keyword-assisted boost for exact technical terms (e.g. RAG, API, grounded)
            doc_lower = doc_text.lower()
            keyword_matches = sum(1 for kw in keywords if kw in doc_lower) if keywords else 0
            keyword_bonus = 0.0
            if keywords and keyword_matches > 0:
                match_ratio = keyword_matches / len(keywords)
                # Boost up to 0.08 based on keyword match
                keyword_bonus = 0.08 * match_ratio

            effective_score = min(1.0, base_score + keyword_bonus)
            effective_dist = max(0.0, 1.0 - effective_score)

            # Filtering against threshold: require semantic similarity within distance threshold,
            # or allow border chunks only if they have strong multi-keyword domain matches (>= 2 keywords and >= 50% ratio)
            is_strong_keyword_match = (
                keywords and keyword_matches >= 2 and (keyword_matches / len(keywords)) >= 0.50
                and effective_dist <= self.distance_threshold
            )
            if raw_dist > self.distance_threshold and not is_strong_keyword_match:
                continue

            if effective_score < self.min_relevance_score:
                continue

            metadata = (
                metadatas[i]
                if i < len(metadatas) and isinstance(metadatas[i], dict)
                else {}
            )

            source_name = metadata.get("source", "Unknown")
            candidates.append({
                "text": doc_text,
                "source": source_name,
                "chunk_id": metadata.get("chunk_id", f"{source_name}_chunk_{i}"),
                "chunk_index": metadata.get("chunk_index", i),
                "citation": metadata.get("citation", source_name),
                "file_type": metadata.get("file_type", "Unknown"),
                "distance": round(raw_dist, 4),
                "relevance_score": round(effective_score, 3),
            })

        # Rank by effective relevance score descending
        candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Strictly return Top-K selection (1, 3, or 5)
        selected_results = candidates[:self.top_k]

        return {
            "query": cleaned_query,
            "query_type": query_type,
            "top_k": self.top_k,
            "results": selected_results,
            "result_count": len(selected_results),
            "status": (
                "success"
                if selected_results
                else "no_relevant_information"
            )
        }