# System Architecture

## Project Title
**Development of AI-Based Knowledge Retrieval Platform with Query Resolution System**
**Infosys Springboard Virtual Internship 7.0**

---

## 1. Executive Architecture Overview

The AI-Based Knowledge Retrieval Platform is an enterprise-grade multi-agent Retrieval-Augmented Generation (RAG) system built to solve accurate, grounded information retrieval from unstructured and semi-structured documents (PDF, DOCX, TXT, CSV).

The system integrates a **Multi-Agent Orchestrator**, a **Sentence-Aware Boundary-Safe Chunking Engine**, a **ChromaDB Vector Store** powered by `sentence-transformers/all-MiniLM-L6-v2`, **Groq LLaMA-3.3-70B-Versatile** for grounded natural language synthesis, **Conversation Memory** with cross-turn pronoun resolution, an **Ambiguity Clarification Agent**, **In-Browser Voice Interaction** (Speech-to-Text & Text-to-Speech), and an **Analytics Engine** for query logging and knowledge gap discovery.

```
                              ┌────────────────────────────────────────────────────────┐
                              │                    USER INTERACTION                    │
                              │     React 19 Dashboard (Voice Input, Audio, UI)        │
                              └───────────────────────────┬────────────────────────────┘
                                                          │ HTTP / JSON
                                                          ▼
                              ┌────────────────────────────────────────────────────────┐
                              │                    FLASK REST API                      │
                              │         /ask  |  /upload  |  /analytics/*              │
                              └───────────────────────────┬────────────────────────────┘
                                                          │
                                                          ▼
                              ┌────────────────────────────────────────────────────────┐
                              │                 MULTI-AGENT ORCHESTRATOR               │
                              │                  (backend/orchestrator.py)             │
                              └───────┬───────────────────┬────────────────────┬───────┘
                                      │                   │                    │
          ┌───────────────────────────┘                   │                    └──────────────────────────┐
          ▼                                               ▼                                               ▼
┌───────────────────────┐                     ┌───────────────────────┐                       ┌───────────────────────┐
│  CONVERSATION MEMORY  │                     │ CLARIFICATION AGENT   │                       │  QUERY UNDERSTANDING  │
│  Session tracking &   │                     │ Ambiguity & missing   │                       │ Intent classification │
│  Pronoun resolution   │                     │ context detection     │                       │ (factual, procedural, │
│ (conversation_memory) │                     │ (clarification_agent) │                       │  comparative, etc.)   │
└───────────────────────┘                     └───────────────────────┘                       └───────────┬───────────┘
                                                                                                          │
                                                                                                          ▼
                                                                                              ┌───────────────────────┐
                                                                                              │    RETRIEVAL AGENT    │
                                                                                              │ all-MiniLM-L6-v2 embs │
                                                                                              │ ChromaDB vector query │
                                                                                              │ Keyword-boost ranking │
                                                                                              └───────────┬───────────┘
                                                                                                          │
                                      ┌───────────────────────────────────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             RESPONSE GENERATION AGENT                                               │
│                                           Groq LLaMA-3.3-70B-Versatile                                              │
│                               Strict Grounding | Citations | Confidence Scoring | Fallbacks                         │
└───────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             ANALYTICS & MONITORING SERVICE                                          │
│                                    Query Telemetry | Knowledge Gap Detection | Trends                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ingestion & Document Processing Pipeline

The ingestion pipeline handles heterogeneous document ingestion, text sanitization, sentence-aware chunking, vector embedding, and deterministic storage in ChromaDB.

```
Raw File (PDF, DOCX, TXT, CSV)
      │
      ▼
Document Reader (backend/document_reader.py)
      │   - PDF: PyMuPDF (fitz) page extraction
      │   - DOCX: python-docx paragraph extraction
      │   - CSV: pandas tabular normalization
      │   - Sanitization: normalize unicode, preserve paragraph structure (\n\n)
      ▼
Sentence-Aware Chunker (backend/chunking.py)
      │   - Target Chunk Size: 500 characters
      │   - Overlap: 50 characters
      │   - Paragraph & Sentence boundary preservation
      │   - Mid-word truncation prevention
      ▼
Embedding Generator (backend/embeddings.py)
      │   - Model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
      │   - Normalization: L2 normalized dense vectors
      ▼
Vector Store (backend/vector_store.py)
          - Database: ChromaDB PersistentClient
          - Collection: knowledge_base
          - Cleanup: Removes prior chunks of the same source before upserting
          - Deterministic IDs: {source}_chunk_{index}
```

---

## 3. Multi-Agent Responsibilities & Interactions

| Agent Component | Primary Responsibilities | Key Methods / Implementation |
| :--- | :--- | :--- |
| **Orchestrator** | Coordinates execution across all agents, session state management, fallback gating, and telemetry dispatch. | `Orchestrator.process_query(query, session_id, top_k, domain)` in `backend/orchestrator.py` |
| **Conversation Memory Agent** | Tracks multi-turn dialogue history, extracts topical context, and resolves cross-turn pronoun references (e.g., *"Tell me about it"* → *"Tell me about ChromaDB"*). | `ConversationMemory.add_exchange()`, `get_relevant_context()`, `_resolve_memory_reference()` in `backend/conversation_memory_agent.py` |
| **Clarification Agent** | Evaluates query ambiguity, vague inputs, and missing entities; prompts user for clarification with clear multi-option follow-up questions. | `ClarificationAgent.evaluate_query()`, `refine_query()` in `backend/clarification_agent.py` |
| **Query Understanding Agent** | Analyzes syntax, extracts semantic keywords, and classifies queries into Factual, Procedural, Comparative, or Ambiguous. | `QueryUnderstandingAgent.classify_query()` in `backend/query_understanding_agent.py` |
| **Retrieval Agent** | Generates query embeddings, retrieves broad candidate pool (`candidate_k = max(top_k * 4, 12)`), eliminates duplicate texts, applies keyword-assisted ranking boost, and enforces cosine distance threshold (0.60). | `RetrievalAgent.retrieve()` in `backend/retrieval_agent.py` |
| **Response Generation Agent** | Synthesizes grounded natural language answers using Groq LLaMA-3.3-70B, computes confidence scores, cites exact file sources, and transparently identifies missing details. | `ResponseGenerationAgent.generate_response()` in `backend/response_generation_agent.py` |
| **Analytics Service** | Persists structured query logs, calculates query resolution statistics, identifies low-confidence searches, and aggregates knowledge gaps. | `AnalyticsService.log_query()`, `get_summary()`, `get_knowledge_gaps()` in `backend/analytics_service.py` |

---

## 4. Query Execution Lifecycle & Decision Tree

When a user submits a query:

1. **Input Normalization & Memory Resolution**:
   - The query is sanitized.
   - The Orchestrator retrieves active session memory. If pronouns (*"it"*, *"this"*, *"that"*) are detected, `_resolve_memory_reference()` checks the recent turn topic and resolves the subject.
2. **Ambiguity & Clarification Gating**:
   - If the query is standalone ambiguous (e.g. *"Tell me about it"* without context, *"what is this"*), the Clarification Agent triggers `status: clarification_required` with an explicit clarification question.
   - If clarification was previously requested and the user responds, `refine_query()` blends the clarification into the target query.
3. **Intent Classification**:
   - The Query Understanding Agent classifies the question into Factual, Procedural, Comparative, or Ambiguous with classification confidence.
4. **Vector Retrieval & Ranking**:
   - The Retrieval Agent embeds the query using `all-MiniLM-L6-v2`.
   - ChromaDB returns top semantic chunks.
   - Candidate filtering removes duplicate content across files and ranks chunks by combined cosine similarity and exact keyword boost.
   - If the best chunk distance exceeds the relevance threshold (0.60) and lacks strong multi-keyword overlap, retrieval returns `no_relevant_information`.
5. **Grounded Response Generation**:
   - If chunks are retrieved, Groq LLaMA-3.3-70B generates a strictly grounded answer based only on retrieved context.
   - The response includes chunk citations, source filenames, and confidence label (`High` > 0.80, `Medium` 0.60–0.80, `Low` < 0.60).
6. **Telemetry & Knowledge Gap Recording**:
   - Every transaction is recorded into `analytics_data.json`.
   - Queries with `no_relevant_information` or `Low` confidence are flagged as actionable knowledge gaps.

---

## 5. Technology Stack Summary

| Layer | Component | Version / Tech | Justification |
| :--- | :--- | :--- | :--- |
| **Frontend** | React + Vite | React 19, Vite 8 | Fast reactive UI, native hooks, instant HMR, high performance. |
| **Styling** | Vanilla CSS | Modern CSS Tokens | Clean dark/light glassmorphic layout, micro-interactions, responsive flex/grid. |
| **Voice Processing** | Web Speech API | Browser Native | Zero-latency browser speech recognition (STT) and speech synthesis (TTS). |
| **Backend Framework** | Flask REST API | Python 3.13, Flask 3.1 | Lightweight, thread-safe microservices with CORS support. |
| **Embeddings** | Sentence Transformers | `all-MiniLM-L6-v2` | Fast 384-dimensional dense semantic vectors with low latency. |
| **Vector Store** | ChromaDB | ChromaDB 1.0 | Embedded persistent vector database with cosine distance indexing. |
| **LLM Inference** | Groq Cloud | `llama-3.3-70b-versatile` | Ultra-fast LPUs (500+ tokens/sec) providing grounded reasoning. |
| **Document Parsers** | PyMuPDF, python-docx, pandas | fitz, docx, pandas | Reliable multi-format text extraction from PDF, Word, TXT, and CSV. |

---

## 6. API Interface Contracts

### 1. `POST /ask`
**Request Payload:**
```json
{
  "query": "How does RAG generate a grounded response?",
  "session_id": "session-123",
  "top_k": 3,
  "domain": "AI",
  "original_query": null,
  "clarification_response": null
}
```
**Response Payload:**
```json
{
  "query": "How does RAG generate a grounded response?",
  "query_type": "procedural",
  "classification_confidence": 0.90,
  "answer": "Retrieval-Augmented Generation (RAG) creates a grounded response by...",
  "sources": ["ai_domain.txt"],
  "confidence": { "label": "Low", "score": 0.465 },
  "retrieved_chunks": [...],
  "top_k": 3,
  "status": "success",
  "routing": "retrieval"
}
```

### 2. `POST /upload`
**Request:** `multipart/form-data` with `file` attachment.
**Response:** `{"message": "File uploaded and indexed successfully", "file_name": "ai_domain.txt", "chunks_stored": 5}`.

### 3. Analytics Endpoints
- `GET /analytics/summary`: Aggregate counts for total queries, successful answers, unanswered queries, low-confidence queries, clarifications, and domain distribution.
- `GET /analytics/statistics`: Granular percentages and resolution metrics.
- `GET /analytics/knowledge-gaps`: List of queries that returned low confidence or no information, aggregated by frequency and domain.
- `GET /analytics/queries?domain=Technology&query_type=factual`: Filtered query telemetry logs.
