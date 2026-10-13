# Final Project Demonstration Script & Presentation Guide

## Project Title
**Development of AI-Based Knowledge Retrieval Platform with Query Resolution System**
**Infosys Springboard Virtual Internship 7.0**

---

## 1. Quick Start Commands (Before Starting Presentation)

Open two terminal windows:

### Terminal 1: Start Backend API
```powershell
cd c:\Users\Dell\Documents\AI-Knowledge-Retrieval-Platform
$env:PYTHONPATH='backend'
backend\.venv\Scripts\python.exe backend\app.py
```
*(The Flask backend will start on `http://127.0.0.1:5000`)*

### Terminal 2: Start Frontend UI
```powershell
cd c:\Users\Dell\Documents\AI-Knowledge-Retrieval-Platform\frontend
npm run dev
```
*(The React application will open on `http://localhost:5173` in your browser)*

---

## 2. 5-Minute Presentation Narrative (What to Say)

### Slide / Opening Introduction (30 seconds)
> *"Respected Evaluators, Good morning/afternoon. Today I am presenting my project for the Infosys Springboard Virtual Internship 7.0: **Development of AI-Based Knowledge Retrieval Platform with Query Resolution System**.*
>
> *In enterprise environments, valuable knowledge is locked inside PDFs, Word documents, text notes, and spreadsheets. Traditional keyword search misses meaning, while direct LLMs often hallucinate.*
>
> *To solve this, I designed and implemented a production-grade **Multi-Agent Retrieval-Augmented Generation (RAG)** platform that combines sentence-aware chunking, persistent ChromaDB vector storage, Groq LLaMA 3.3 70B grounded reasoning, conversational memory, voice interaction, and automated knowledge gap analytics."*

---

## 3. Step-by-Step Live Demonstration Sequence (12 Steps)

Follow this exact click-by-click sequence during your demo:

---

### Step 1: Document Ingestion & Knowledge Base Overview
- **Action on Screen:** Show the "Knowledge Base" and "Upload" sections on the dashboard. Point out the indexed files (`technology.txt`, `ai_domain.txt`, `education_domain.txt`, `sample.pdf`).
- **What to Say:**
  > *"First, our platform supports multi-format document ingestion across PDF, DOCX, TXT, and CSV. We implemented sentence-aware boundary-safe chunking that preserves paragraph structures without cutting sentences or words in half. Chunks are embedded using Sentence-Transformers and indexed in a local, persistent ChromaDB vector store."*

---

### Step 2: Factual Query (Technology Domain)
- **Action on Screen:** In the search box, type:
  ```text
  What is ChromaDB?
  ```
  Click **Submit** (or press Enter).
- **Expected Result:** Instant answer explaining that ChromaDB is a vector database that stores embeddings.
- **Show Evaluators:**
  - The answer card.
  - The **Sources** badge showing `technology.txt`.
  - The **Confidence Score** (Medium / High).
- **What to Say:**
  > *"Here, the Query Understanding Agent classified this as a Factual query. The Retrieval Agent pulled the exact chunk from ChromaDB, and Groq LLaMA 3.3 70B synthesized a strictly grounded response with explicit source attribution and confidence scoring."*

---

### Step 3: Conversational Memory & Pronoun Resolution
- **Action on Screen:** In the same session, type:
  ```text
  Tell me more about it
  ```
  Click **Submit**.
- **Expected Result:** The system resolves *"it"* to ChromaDB and provides an in-depth follow-up explanation.
- **Show Evaluators:**
  - Notice the query resolution under transparency: *"Tell me more about ChromaDB"*.
- **What to Say:**
  > *"Notice that I did not repeat the word 'ChromaDB'. Our Conversation Memory Agent tracks session history, identifies the contextual pronoun 'it', and automatically resolves the reference to ChromaDB, maintaining conversational continuity without manual prompt engineering."*

---

### Step 4: Domain Switching & Context Adaptation
- **Action on Screen:** Type:
  ```text
  What is Machine Learning?
  ```
  Click **Submit**.
- **Expected Result:** Returns a comprehensive definition citing `ai_domain.txt` with High confidence.
- **What to Say:**
  > *"When the user transitions to another subject, the Memory Agent recognizes the shift, clears previous pronoun bindings, and adapts to the Education and AI domain seamlessly."*

---

### Step 5: Comparative Query Resolution
- **Action on Screen:** Type:
  ```text
  What is the difference between supervised and unsupervised learning?
  ```
  Click **Submit**.
- **Expected Result:** Returns a structured comparison contrasting labeled data (Supervised) vs unlabeled patterns (Unsupervised).
- **Show Evaluators:**
  - Query Type badge shows: **Comparative**.
- **What to Say:**
  > *"Here, our Query Understanding Agent classified this as a Comparative query. The system retrieved both relevant chunks and synthesized a clear, side-by-side comparison without requiring manual multi-part clarification."*

---

### Step 6: Procedural RAG Query Resolution
- **Action on Screen:** Type:
  ```text
  How does RAG generate a grounded response?
  ```
  Click **Submit**.
- **Expected Result:** Explains the two-step retrieval-then-generation process, citing `ai_domain.txt`.
- **What to Say:**
  > *"This procedural query demonstrates our retrieval optimization. Previously, multi-topic cramming caused this query to fail. With our sentence-aware chunking and keyword-assisted ranking boost, it ranks number one with 100% accuracy."*

---

### Step 7: Ambiguity Detection & Clarification Agent
- **Action on Screen:** Click **New Session** (or refresh page), then type:
  ```text
  Tell me about it
  ```
  Click **Submit**.
- **Expected Result:** The system does NOT pretend to answer. Instead, it displays the **Clarification Box** with:
  > *"Could you specify which topic or concept you want to know about?"*
- **What to Say:**
  > *"When there is no prior context and the user provides an ambiguous question, our Clarification Agent steps in. Instead of hallucinating, the system proactively asks for clarification to resolve the missing intent."*

---

### Step 8: Clarification Refinement
- **Action on Screen:** In the clarification prompt, type or select:
  ```text
  Artificial Intelligence
  ```
  Click **Submit Clarification**.
- **Expected Result:** Answers the refined query about Artificial Intelligence using `ai_domain.txt`.
- **What to Say:**
  > *"Once the user clarifies, the agent refines the query and immediately executes the retrieval pipeline."*

---

### Step 9: Unsupported Query & Zero-Hallucination Honesty
- **Action on Screen:** Type an out-of-domain query:
  ```text
  What is quantum computing?
  ```
  Click **Submit**.
- **Expected Result:**
  - Status: `no_relevant_information`.
  - Answer: *"I could not find sufficient information in the current knowledge base to answer this question."*
  - Sources: None (`[]`).
  - Confidence: `Low (0.0)`.
- **What to Say:**
  > *"This is one of the most critical enterprise features: hallucination prevention. Because 'quantum computing' is not in our knowledge base, our distance threshold filter and strict prompt constraints prevent the model from guessing. It returns an honest refusal, and logs the query for content curators."*

---

### Step 10: Multimodal Voice Input (Speech-to-Text)
- **Action on Screen:** Click the **Microphone** button. Speak into your mic:
  > *"What is an API?"*
- **Expected Result:** Speech is transcribed in real-time into the text box and the search executes automatically.
- **What to Say:**
  > *"We also integrated the browser-native Web Speech API. Users can speak naturally hands-free with zero additional server latency."*

---

### Step 11: Text-to-Speech (Audio Output)
- **Action on Screen:** Click the **Speaker / Audio** icon on the resulting answer card.
- **Expected Result:** Browser speaks the generated answer aloud cleanly.
- **What to Say:**
  > *"The platform also provides full auditory accessibility through native Text-to-Speech synthesis."*

---

### Step 12: Analytics Dashboard & Knowledge Gap Discovery
- **Action on Screen:** Click on the **Analytics** tab at the top.
- **Show Evaluators:**
  1. **Total Queries & Success Rate** cards.
  2. **Query Type Breakdown** chart (Factual, Procedural, Comparative).
  3. **Knowledge Gaps Table:** Point out `what is quantum computing?` sitting right at the top of the knowledge gaps list!
- **What to Say:**
  > *"Finally, here is our Analytics Engine. Every query is logged with telemetry. Content administrators can see resolution statistics and immediately identify what users are asking for that is missing from documentation—such as our quantum computing query recorded right here. This transforms the platform from a search engine into an active knowledge management system."*

---

## 4. Concluding Statement (30 seconds)
> *"In summary, the platform successfully delivers:
> 1. Multi-format ingestion with sentence-aware chunking,
> 2. Persistent ChromaDB vector search with 100% Top-K accuracy,
> 3. Autonomous agents for memory, clarification, retrieval, and grounded Groq LLaMA 3.3 generation,
> 4. Multimodal voice input and text-to-speech, and
> 5. Real-time query analytics and knowledge gap detection.
>
> All objectives of the Infosys Springboard Virtual Internship 7.0 have been fully met and verified. Thank you, and I am happy to answer any questions!"*

---

## 5. Potential Evaluator Questions & Ready Answers

**Q1: How do you prevent the LLM from hallucinating?**
> *A: We use a multi-tiered guardrail: first, a cosine distance threshold of 0.60 in ChromaDB rejects out-of-domain chunks. Second, the system prompt strictly instructs Groq LLaMA 3.3 70B to use ONLY the retrieved context and explicitly declare missing information.*

**Q2: Why did you choose Sentence-Transformers (`all-MiniLM-L6-v2`) over OpenAI embeddings?**
> *A: `all-MiniLM-L6-v2` runs entirely on-premise/locally with zero API subscription cost, produces compact 384-dimensional vectors with high semantic fidelity, and offers sub-20ms embedding latency on CPU.*

**Q3: How does the Conversation Memory Agent resolve pronouns?**
> *A: It maintains session history. When an ambiguous phrase or pronoun like 'it', 'this', or 'that' is detected, it inspects the prior turn's topic and replaces the pronoun with the concrete subject before routing to retrieval.*

**Q4: What was the main retrieval bottleneck you solved in M4.3?**
> *A: Previously, fixed-character chunking cut sentences mid-phrase and packed unrelated topics together, which diluted semantic vectors. We redesigned the chunker to be sentence-aware and paragraph-preserving, boosting accuracy to 100%.*
