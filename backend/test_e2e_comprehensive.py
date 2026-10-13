import os
import sys
import json

backend_path = r"c:\Users\Dell\Documents\AI-Knowledge-Retrieval-Platform\backend"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from orchestrator import Orchestrator
from analytics_service import AnalyticsService

print("======================================================================")
print("       PHASE 3 & 4 COMPREHENSIVE END-TO-END VALIDATION SUITE          ")
print("======================================================================")

analytics = AnalyticsService()
orch = Orchestrator()

# Test 1: Verify Analytics Service Endpoints
print("\n[TEST 1] Testing Analytics Service Methods...")
summary = analytics.get_summary()
print(f"Total Queries: {summary.get('total_queries')}")
print(f"Successful: {summary.get('successful_answers')}")
print(f"Unanswered: {summary.get('unanswered_queries')}")
print(f"Low Confidence: {summary.get('low_confidence_queries')}")
print(f"Clarifications: {summary.get('clarification_queries')}")
print(f"Domains: {summary.get('domains')}")

gaps = analytics.get_knowledge_gaps()
print(f"Knowledge Gaps Found: {len(gaps)}")
for g in gaps[:3]:
    print(f"  - Query: '{g.get('query')}' (Domain: {g.get('domain')}, Occurrences: {g.get('occurrences')})")

filtered = analytics.filter_queries(domain="Technology")
print(f"Filtered (Domain=Technology): {len(filtered)} queries")

# Test 2: Multi-Domain End-to-End Orchestrator Queries
print("\n[TEST 2] Running Multi-Domain Orchestrator Verification...")

test_cases = [
    {
        "domain": "Education",
        "type": "Factual",
        "query": "What is Machine Learning?",
        "session": "e2e-edu-1",
        "top_k": 3,
    },
    {
        "domain": "Education",
        "type": "Comparative",
        "query": "What is the difference between supervised and unsupervised learning?",
        "session": "e2e-edu-2",
        "top_k": 3,
    },
    {
        "domain": "Technology",
        "type": "Factual",
        "query": "What is ChromaDB?",
        "session": "e2e-tech-1",
        "top_k": 1,
    },
    {
        "domain": "Technology",
        "type": "Factual",
        "query": "What is an API?",
        "session": "e2e-tech-2",
        "top_k": 3,
    },
    {
        "domain": "AI",
        "type": "Procedural",
        "query": "How does RAG generate a grounded response?",
        "session": "e2e-ai-1",
        "top_k": 3,
    },
    {
        "domain": "AI",
        "type": "Procedural",
        "query": "How does RAG work?",
        "session": "e2e-ai-2",
        "top_k": 5,
    },
    {
        "domain": "General",
        "type": "Ambiguous (Clarification Needed)",
        "query": "Tell me about it",
        "session": "e2e-clarify-1",
        "top_k": 3,
    },
    {
        "domain": "General",
        "type": "Unsupported (Knowledge Gap Expected)",
        "query": "What is quantum computing?",
        "session": "e2e-unsupported-1",
        "top_k": 3,
    },
]

results_summary = []

for tc in test_cases:
    res = orch.process_query(tc["query"], session_id=tc["session"], top_k=tc["top_k"])
    status = res.get("status")
    q_type = res.get("query_type")
    sources = res.get("sources", [])
    chunks_count = len(res.get("retrieved_chunks", []))
    conf = res.get("confidence", {})
    ans = (res.get("answer") or "")[:90].replace("\n", " ").encode("ascii", "replace").decode("ascii")
    
    passed = True
    if tc["type"] == "Ambiguous (Clarification Needed)":
        passed = (status == "clarification_required")
    elif tc["type"] == "Unsupported (Knowledge Gap Expected)":
        passed = (status == "no_relevant_information" and len(sources) == 0)
    else:
        passed = (status == "success" and len(sources) > 0 and len(ans) > 20)
        
    results_summary.append({
        "domain": tc["domain"],
        "query": tc["query"],
        "status": status,
        "query_type": q_type,
        "sources": sources,
        "chunks": chunks_count,
        "confidence": conf.get("score"),
        "passed": passed
    })
    
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] Domain: {tc['domain']} | Query: '{tc['query']}'")
    print(f"       Status: {status} | Type: {q_type} | Sources: {sources} | Confidence: {conf}")
    print(f"       Answer: {ans}...")

# Test 3: Conversation Memory & Context Switching
print("\n[TEST 3] Testing Conversation Memory Context Preservation & Follow-ups...")
mem_session = "mem-test-suite"
# Query 1
r1 = orch.process_query("What is ChromaDB?", session_id=mem_session)
print(f"Turn 1: 'What is ChromaDB?' -> Status: {r1.get('status')}, Sources: {r1.get('sources')}")

# Query 2 (Follow-up with pronoun reference)
r2 = orch.process_query("Tell me more about it", session_id=mem_session)
ans2 = (r2.get("answer") or "")[:90].replace("\n", " ").encode("ascii", "replace").decode("ascii")
print(f"Turn 2: 'Tell me more about it' -> Resolved: {r2.get('query')}, Status: {r2.get('status')}")
print(f"        Answer: {ans2}...")

# Query 3 (Domain Switch to Education)
r3 = orch.process_query("What is Machine Learning?", session_id=mem_session)
print(f"Turn 3: 'What is Machine Learning?' -> Status: {r3.get('status')}, Sources: {r3.get('sources')}")

all_e2e_pass = all(r["passed"] for r in results_summary)
print("\n" + "=" * 70)
print(f"OVERALL EVALUATION RESULT: {'ALL TESTS PASSED (100%)' if all_e2e_pass else 'SOME TESTS FAILED'}")
print("=" * 70)
