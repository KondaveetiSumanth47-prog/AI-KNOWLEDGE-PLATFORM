import json
from datetime import datetime
from pathlib import Path
from collections import Counter


ANALYTICS_FILE = Path(__file__).resolve().parent / "analytics_data.json"


class AnalyticsService:

    def __init__(self, file_path=None):
        self.file_path = Path(file_path) if file_path else ANALYTICS_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            self.file_path.write_text(
                json.dumps([], indent=2),
                encoding="utf-8"
            )

    def _load_data(self):
        self._ensure_file()

        try:
            content = self.file_path.read_text(
                encoding="utf-8"
            )

            if not content.strip():
                return []

            data = json.loads(content)

            return data if isinstance(data, list) else []

        except (json.JSONDecodeError, OSError):
            return []

    def _save_data(self, data):
        self.file_path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    def record_query(
        self,
        query,
        query_type="unknown",
        status="unknown",
        confidence=None,
        retrieved_results=None,
        sources=None,
        clarification_required=False,
        session_id="default-session",
        domain="unknown",
        routing="unknown"
    ):
        retrieved_results = (
            retrieved_results
            if isinstance(retrieved_results, list)
            else []
        )

        sources = (
            sources
            if isinstance(sources, list)
            else []
        )

        confidence = (
            confidence
            if isinstance(confidence, dict)
            else {}
        )

        confidence_label = confidence.get(
            "label",
            "Unknown"
        )

        confidence_score = confidence.get(
            "score",
            0
        )

        try:
            confidence_score = float(
                confidence_score
            )
        except (TypeError, ValueError):
            confidence_score = 0.0

        record = {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "session_id": session_id,
            "query": str(query or ""),
            "query_type": str(
                query_type or "unknown"
            ),
            "status": str(
                status or "unknown"
            ),
            "confidence": {
                "label": confidence_label,
                "score": round(
                    confidence_score,
                    3
                )
            },
            "retrieved_result_count": len(
                retrieved_results
            ),
            "sources": sources,
            "clarification_required": bool(
                clarification_required
            ),
            "domain": str(
                domain or "unknown"
            ),
            "routing": str(
                routing or "unknown"
            ),
        }

        data = self._load_data()
        data.append(record)
        self._save_data(data)

        return record

    def get_all_queries(self):
        return self._load_data()

    def filter_queries(
        self,
        domain=None,
        query_type=None,
        date=None,
        confidence=None,
        status=None
    ):
        data = self._load_data()
        results = []

        for item in data:
            if domain and str(item.get("domain", "")).lower() != str(domain).lower():
                continue
            if query_type and str(item.get("query_type", "")).lower() != str(query_type).lower():
                continue
            if status and str(item.get("status", "")).lower() != str(status).lower():
                continue
            if confidence:
                conf_label = str(item.get("confidence", {}).get("label", "")).lower()
                if conf_label != str(confidence).lower():
                    continue
            if date:
                ts = str(item.get("timestamp", ""))
                if not ts.startswith(str(date)):
                    continue
            results.append(item)

        return results

    def get_summary(self):
        data = self._load_data()

        total_queries = len(data)

        successful = sum(
            1
            for item in data
            if item.get("status") == "success"
        )

        unanswered = sum(
            1
            for item in data
            if item.get("status")
            in {
                "no_relevant_information",
                "unanswered",
            }
        )

        low_confidence = sum(
            1
            for item in data
            if str(
                item.get(
                    "confidence",
                    {}
                ).get(
                    "label",
                    ""
                )
            ).lower()
            == "low"
        )

        clarification_count = sum(
            1
            for item in data
            if item.get(
                "clarification_required",
                False
            )
        )

        query_types = Counter(
            item.get(
                "query_type",
                "unknown"
            )
            for item in data
        )

        domains = Counter(
            item.get(
                "domain",
                "unknown"
            )
            for item in data
        )

        return {
            "total_queries": total_queries,
            "successful_answers": successful,
            "unanswered_queries": unanswered,
            "low_confidence_queries": low_confidence,
            "clarification_queries": clarification_count,
            "query_types": dict(query_types),
            "domains": dict(domains),
        }

    def get_knowledge_gaps(self):
        data = self._load_data()

        gaps = {}

        for item in data:

            status = str(
                item.get(
                    "status",
                    ""
                )
            ).lower()

            confidence = item.get(
                "confidence",
                {}
            )

            confidence_label = str(
                confidence.get(
                    "label",
                    ""
                )
            ).lower()

            is_gap = (
                status
                in {
                    "no_relevant_information",
                    "unanswered",
                }
                or confidence_label == "low"
            )

            if not is_gap:
                continue

            query = str(
                item.get(
                    "query",
                    ""
                )
            ).strip()

            if not query:
                continue

            key = query.lower()

            if key not in gaps:
                gaps[key] = {
                    "query": query,
                    "domain": item.get(
                        "domain",
                        "unknown"
                    ),
                    "occurrences": 0,
                    "low_confidence_count": 0,
                    "unanswered_count": 0,
                }

            gaps[key][
                "occurrences"
            ] += 1

            if confidence_label == "low":
                gaps[key][
                    "low_confidence_count"
                ] += 1

            if status in {
                "no_relevant_information",
                "unanswered",
            }:
                gaps[key][
                    "unanswered_count"
                ] += 1

        return list(
            gaps.values()
        )

    def get_statistics(self):
        return {
            "summary": self.get_summary(),
            "knowledge_gaps": (
                self.get_knowledge_gaps()
            ),
            "total_records": len(
                self._load_data()
            ),
        }


analytics_service = AnalyticsService()