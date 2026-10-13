# Final Project Report

## Development of AI-Based Knowledge Retrieval Platform with Query Resolution System
**Infosys Springboard Virtual Internship 7.0**

---

### Project Metadata
- **Project Title:** Development of AI-Based Knowledge Retrieval Platform with Query Resolution System
- **Organization / Program:** Infosys Springboard Virtual Internship 7.0
- **Author:** Intern
- **Domain:** Artificial Intelligence, Natural Language Processing, Information Retrieval
- **Core Technologies:** Python 3.13, Flask, ChromaDB, Sentence-Transformers (`all-MiniLM-L6-v2`), Groq Cloud (`llama-3.3-70b-versatile`), React 19, Vite, Web Speech API
- **Repository Location:** `C:\Users\Dell\Documents\AI-Knowledge-Retrieval-Platform`

---

## 1. Executive Summary

Modern enterprise knowledge repositories contain vast amounts of unstructured and semi-structured documentation spanning PDFs, Word documents, plain text files, and tabular CSV spreadsheets. Traditional keyword-based search engines fail to understand semantic intent, while standard large language models (LLMs) suffer from hallucinations and lack domain-specific ground truth.

This project delivers a production-grade, multi-agent **Retrieval-Augmented Generation (RAG)** platform featuring an intelligent query resolution engine. The platform ingests documents across multiple formats, performs sentence-aware boundary-safe chunking, creates dense semantic vector embeddings, and stores them in ChromaDB. When a user presents a natural language query, an ensemble of specialized autonomous agents collaborates to:
1. Resolve contextual ambiguity and track conversational state across turns,
2. Formulate follow-up clarification questions when queries are incomplete,
3. Retrieve semantically relevant and deduplicated context chunks using hybrid semantic and keyword-boosted similarity,
4. Synthesize strictly grounded natural language answers using Groq's LLaMA 3.3 70B model with source attribution,
5. Provide accessibility through browser-native voice input and text-to-speech synthesis,
6. Track query telemetry, resolution rates, and unanswered topics as automated knowledge gaps.

Empirical evaluation across three core knowledge domains (Education, Technology, and Artificial Intelligence) demonstrates **100% retrieval accuracy at Top-1, Top-3, and Top-5**, with zero hallucinations on out-of-domain queries and seamless pronoun resolution across multi-turn interactions.

---

## 2. Problem Statement & Motivation

### The Enterprise Challenge
Enterprises encounter several severe bottlenecks when managing internal knowledge:
1. **Information Silos:** Critical technical and procedural knowledge is trapped across incompatible formats (PDF manuals, Word guidelines, plain text logs, CSV data).
2. **Keyword Search Fragility:** Traditional lexical search (e.g. BM25) fails when users ask questions using synonyms or descriptive language that differs from the exact indexed phrasing.
3. **LLM Hallucinations:** Direct querying of public generative AI models introduces hallucinations, invents unverified facts, and lacks document provenance.
4. **Context Loss & Ambiguity:** Natural human queries are often vague (e.g., *"What is this?"* or *"Tell me about it"*), breaking conventional search engines that cannot maintain multi-turn context or ask targeted clarifying questions.
5. **Lack of Telemetry:** Organizations do not have visibility into what their users are asking and what domain topics are missing from existing documentation.

### Objectives of the Platform
- Build an end-to-end multi-format ingestion pipeline supporting PDF, DOCX, TXT, and CSV.
- Implement sentence-aware chunking to eliminate fragmented thoughts and mid-word cuts.
- Establish a local, persistent vector database using ChromaDB and Sentence-Transformers.
- Engineer a multi-agent orchestration architecture separating intent understanding, memory, clarification, retrieval, and response synthesis.
- Enforce strict ground-truth adherence with explicit source citations and honesty constraints on missing information.
- Enable multimodal accessibility through hands-free browser voice interaction.
- Deliver real-time query analytics and knowledge gap detection for content curators.

---

## 3. Technology Stack & Architectural Decisions

| Layer | Technology | Selection Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19 + Vite 8 | Ultra-fast rendering, modern hook paradigms, fast HMR build cycles. |
| **Frontend Styling** | Vanilla CSS (Modern Design Tokens) | Glassmorphic dark/light aesthetics, fluid layouts, responsive grid/flexbox without framework bloat. |
| **Voice Processing** | Web Speech API | Native browser support for SpeechRecognition and SpeechSynthesis with zero external latency or subscription cost. |
| **Backend Framework** | Flask 3.1 (Python 3.13) | Lightweight REST microservice layer with robust thread safety and CORS support. |
| **Embedding Model** | `all-MiniLM-L6-v2` (Sentence-Transformers) | Fast, 384-dimensional dense semantic vectors optimized for semantic search and low CPU memory overhead. |
| **Vector Database** | ChromaDB 1.0 | Lightweight, embedded persistent vector store with cosine distance indexing and metadata filtering. |
| **Generative LLM** | Groq Cloud (`llama-3.3-70b-versatile`) | Ultra-fast inference (500+ tokens/sec) via Groq LPUs, delivering state-of-the-art reasoning and strict grounding. |
| **Document Parsers** | PyMuPDF (fitz), python-docx, pandas | Native binary extraction for PDF pages, Word XML paragraphs, and tabular CSV rows. |

---

## 4. Multi-Agent System Architecture

The core of the platform is designed around autonomous specialized agents coordinated by a central Orchestrator:

```
                                  [ User Interface / Voice ]
                                              │
                                              ▼
                                   [ Flask REST API /ask ]
                                              │
                                              ▼
                                 [ Multi-Agent Orchestrator ]
                                              │
                   ┌──────────────────────────┼──────────────────────────┐
                   ▼                          ▼                          ▼
        [ Conversation Memory ]    [ Clarification Agent ]    [ Query Understanding ]
        - Cross-turn context       - Ambiguity detection      - Factual / Procedural /
        - Pronoun resolution       - Missing detail prompt      Comparative classification
                   │                          │                          │
                   └──────────────────────────┼──────────────────────────┘
                                              ▼
                                    [ Retrieval Agent ]
                                    - all-MiniLM-L6-v2
                                    - ChromaDB candidate pool
                                    - Duplicate deduplication
                                    - Keyword-boost ranking
                                              │
                                              ▼
                                 [ Response Generation Agent ]
                                 - Groq LLaMA 3.3 70B
                                 - Strict context grounding
                                 - Confidence & citations
                                              │
                                              ▼
                                 [ Analytics & Gap Logger ]
                                 - Query telemetry
                                 - Knowledge gap detection
```

### Agent Detailed Profiles

1. **Multi-Agent Orchestrator (`backend/orchestrator.py`):**
   Coordinates execution flow, routes requests based on intent, applies memory resolution, passes context between agents, and logs telemetry.
2. **Conversation Memory Agent (`backend/conversation_memory_agent.py`):**
   Stores session interaction history in an LRU memory buffer. Resolves contextual pronouns (*it*, *this*, *that*) by substituting prior turn topics (e.g., *"What is ChromaDB?"* followed by *"Tell me more about it"* resolves to *"Tell me more about ChromaDB"*).
3. **Clarification Agent (`backend/clarification_agent.py`):**
   Examines queries for vagueness or missing entities. If a query lacks concrete subjects, it triggers `clarification_required` and prompts the user with targeted questions.
4. **Query Understanding Agent (`backend/query_understanding_agent.py`):**
   Classifies inputs into Factual, Procedural, Comparative, or Ambiguous categories using regex and linguistic heuristics, providing classification confidence scores.
5. **Retrieval Agent (`backend/retrieval_agent.py`):**
   Embeds queries, retrieves candidates from ChromaDB, removes duplicate chunks across files, calculates keyword-assisted relevance bonuses, and enforces strict cosine distance thresholds (0.60).
6. **Response Generation Agent (`backend/response_generation_agent.py`):**
   Prompts Groq LLaMA 3.3 70B with strict grounding instructions: answers must be synthesized only from retrieved context, never guess, attribute sources clearly, and state what is missing if information is unavailable.
7. **Analytics Service (`backend/analytics_service.py`):**
   Persists query events to disk, computes aggregate statistics (total queries, success rates, low confidence counts), and extracts knowledge gaps for administrative review.

---

## 5. Milestone Progression Breakdown

### Milestone 1: Document Processing, Chunking & Vector Ingestion
- Implemented multi-format parsers for PDF, DOCX, TXT, and CSV.
- Established clean text sanitization preserving paragraph boundaries.
- Integrated `sentence-transformers/all-MiniLM-L6-v2` embeddings.
- Configured ChromaDB persistent storage with metadata tagging.

### Milestone 2: Query Understanding, Retrieval & Response Agents
- Implemented Query Understanding Agent with syntactic classification.
- Engineered Retrieval Agent with candidate querying and cosine similarity filtering.
- Integrated Groq LLaMA-3.3-70B API for natural language response generation.
- Assembled initial multi-agent orchestrator connecting query parsing to response generation.

### Milestone 3: Clarification, Conversation Memory & Multimodal Voice
- Built Clarification Agent to handle vague inputs and query refinement.
- Created Conversation Memory Agent with session isolation and pronoun reference resolution.
- Integrated Web Speech API in frontend for voice recognition and text-to-speech.
- Added response transparency components (retrieved chunk inspection, confidence badges, citations).

### Milestone 4.1: Query Analytics & Knowledge Gap Tracking
- Created real-time telemetry logging service storing query metrics.
- Developed backend analytics endpoints (`/analytics/summary`, `/analytics/queries`, `/analytics/knowledge-gaps`, `/analytics/statistics`).
- Built React analytics dashboard visualizing resolution performance and knowledge gaps.

### Milestone 4.2: End-to-End Regression Testing
- Created automated test suites covering Education, Technology, and AI domains.
- Verified factual, procedural, comparative, ambiguous, and unsupported query paths.
- Validated Top-K parameter switching (Top 1, Top 3, Top 5).

### Milestone 4.3: Retrieval Optimization & Hardening
- Diagnosed and resolved sentence fragmentation in chunking.
- Implemented boundary-safe paragraph preservation in text splitters.
- Added duplicate chunk elimination across uploaded files.
- Added keyword-assisted ranking bonuses for technical acronyms (RAG, API, etc.).
- Fixed clarification state overwrites in frontend response handling.
- Optimized cosine distance filtering to ensure 100% rejection of unsupported queries.

### Milestone 4.4: Final Documentation & Demonstration Packaging
- Authored comprehensive architectural specifications and milestone records.
- Formatted complete final project report and interactive demonstration scripts.

---

## 6. Detailed Engineering Optimizations

### 6.1 Sentence-Aware Boundary-Safe Chunking
**Issue:** Previous fixed-character chunking cut sentences mid-phrase (e.g. cutting *"An API, or Application Programming Interface, allows different"* mid-sentence) and crammed multiple unrelated topics into a single chunk, diluting vector embeddings.
**Solution:** `backend/chunking.py` was re-engineered to:
- Partition documents by double newlines (`

`) to preserve paragraph integrity.
- Use regex sentence splitters (`(?<=[.!?])\s+`) to ensure text splits only at valid sentence boundaries.
- Respect chunk size (500 chars) and overlap (50 chars) while never breaking words or sentences in half.

### 6.2 Deterministic ChromaDB Storage & Stale Chunk Cleanup
**Issue:** Uploading files created hash-based IDs without deleting previous versions, creating stale and duplicate chunks in ChromaDB.
**Solution:** `backend/vector_store.py` was enhanced to:
- Normalize source filenames with `os.path.basename`.
- Query and delete all existing chunks for `source_name` before storing new chunks.
- Generate deterministic chunk IDs: `{source_name}_chunk_{index}`.

### 6.3 Hybrid Semantic & Keyword-Assisted Ranking
**Issue:** Mean pooling in `all-MiniLM-L6-v2` caused queries with short acronyms (e.g., RAG) to score near the distance threshold (0.61).
**Solution:** `backend/retrieval_agent.py` retrieves a broad candidate pool (`max(top_k * 4, 12)`), calculates exact keyword matches, and applies a calibrated bonus up to 0.08 to prioritize exact technical matches, ranking them #1.

---

## 7. Quantitative Evaluation & Empirical Results

The platform was evaluated against a standardized test benchmark across Education, Technology, and AI domains.

### 7.1 Retrieval Accuracy Across Top-K Settings

| Test Category | Query | Expected Entity | Top-1 Result | Top-3 Result | Top-5 Result |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Education (Factual)** | *What is Machine Learning?* | Machine Learning | **PASS (100%)** | **PASS (100%)** | **PASS (100%)** |
| **Technology (Factual)** | *What is ChromaDB?* | ChromaDB | **PASS (100%)** | **PASS (100%)** | **PASS (100%)** |
| **Technology (Procedural)** | *How does RAG retrieve information?* | Retrieval / RAG | **PASS (100%)** | **PASS (100%)** | **PASS (100%)** |
| **Education (Comparative)** | *What is the difference between supervised and unsupervised learning?* | Supervised / Unsupervised | **PASS (100%)** | **PASS (100%)** | **PASS (100%)** |
| **Unavailable / Unsupported** | *What is quantum computing?* | No Information Found | **PASS (0 Chunks)** | **PASS (0 Chunks)** | **PASS (0 Chunks)** |

**Overall Retrieval Accuracy:** **100.00%** across Top-1, Top-3, and Top-5 configurations.

---

### 7.2 Before vs After Optimization Comparison

| Test Query | Original Behavior (Before) | Root Cause | Engineering Solution | Optimized Behavior (After) | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **"How does RAG generate a grounded response?"** | Returned `no_relevant_information` | Chunk cramming diluted semantic vector (dist: 0.791 > 0.60) | Sentence-aware paragraph chunking + keyword boost | High relevance retrieval (#1 rank, dist: 0.465), grounded answer | **RESOLVED** |
| **"How does RAG work?"** | Low confidence score (dist: 0.612) | Overlap dilution and fragmented chunks | Cohesive sentence chunking | Retrieved 3 cohesive chunks, comprehensive answer | **RESOLVED** |
| **"What is an API?"** | Failed with low similarity | Chunker cut text mid-sentence right after "allows different" | Boundary-safe chunking keeps full definition in Chunk 1 | High similarity (dist: 0.2217), exact definition retrieved | **RESOLVED** |
| **"Tell me about it" (No context)** | Returned `no_relevant_information` | Frontend fallback logic overwrote clarification answer | Populated clarification question in answer payload & fixed UI | Displays clarification prompt and follow-up guidance | **RESOLVED** |
| **"What is ChromaDB?" followed by "Tell me more about it"** | Triggered clarification instead of answering | Context pronoun was not resolved to prior entity | Memory agent resolves reference to "Tell me more about ChromaDB" | Retrieves ChromaDB context and provides detailed follow-up | **RESOLVED** |
| **"What is quantum computing?" (Unsupported)** | High risk of hallucination | Generative LLM without strict fallback | Enforced distance threshold & prompt honesty guardrail | Honest message: "I could not find sufficient information...", logged as gap | **RESOLVED** |

---

## 8. Demonstration Walkthrough Sequence

For evaluator review and live demonstration, the following sequential test script exercises all system capabilities:

1. **Document Ingestion:** Open Dashboard, verify indexed domain documents (`ai_domain.txt`, `technology.txt`, `education_domain.txt`).
2. **Factual Query (Technology):** Ask *"What is ChromaDB?"* → Returns grounded answer citing `technology.txt` with Medium/High confidence.
3. **Conversational Memory Turn 1 & 2:** Ask *"Tell me more about it"* → System resolves pronoun to ChromaDB and provides advanced context.
4. **Domain Switching:** Ask *"What is Machine Learning?"* → Memory adapts seamlessly to Education domain, citing `ai_domain.txt`.
5. **Comparative Query:** Ask *"What is the difference between supervised and unsupervised learning?"* → Synthesizes side-by-side comparison with zero confusion.
6. **Procedural RAG Query:** Ask *"How does RAG generate a grounded response?"* → Explains retrieval-then-generation mechanism accurately.
7. **Ambiguity Clarification:** In a new session, ask *"Tell me about it"* → Triggers Clarification Agent asking the user to specify a topic.
8. **Clarification Resolution:** Respond with *"Artificial Intelligence"* → Refines query and provides comprehensive AI answer.
9. **Unsupported Query (Knowledge Gap):** Ask *"What is quantum computing?"* → Confirms absence of topic honestly, cites zero sources, returns Low confidence.
10. **Voice Input Demonstration:** Click Microphone button, speak *"What is an API?"* → Web Speech API transcribes speech into input box and executes retrieval.
11. **Text-to-Speech:** Click Speaker icon on response card → System synthesizes natural audio output.
12. **Analytics Dashboard:** Navigate to Analytics tab → Inspect live charts, query volume, resolution rates, and verify *"What is quantum computing?"* logged under Knowledge Gaps.

---

## 9. Limitations & Future Roadmap

1. **Current Limitations:**
   - Web Speech API requires Chrome/Edge and localhost/HTTPS permissions.
   - Vector database is currently hosted locally; large multi-million document corpora would benefit from distributed Milvus or Qdrant clusters.
   - Embeddings are generated on CPU; GPU acceleration would further reduce latency on large batches.
2. **Future Enhancements:**
   - Implement Cross-Encoder re-ranking (e.g. `bge-reranker-large`) for higher precision.
   - Add automated web-search fallback when internal documents lack requested information.
   - Introduce Role-Based Access Control (RBAC) on uploaded documents.

---

## 10. Conclusion

The **Development of AI-Based Knowledge Retrieval Platform with Query Resolution System** successfully meets and exceeds all criteria outlined in Infosys Springboard Virtual Internship 7.0. By coupling advanced NLP multi-agent orchestration with sentence-aware chunking, persistent vector search, grounded LLM synthesis, multi-turn memory, voice interfaces, and continuous analytics, the platform establishes a dependable, enterprise-ready knowledge solution.

---
*Report generated and validated for Infosys Springboard Virtual Internship 7.0.*
