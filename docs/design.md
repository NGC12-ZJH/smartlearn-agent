# SmartLearn Agent — Product Design

> **Author:** Jinghan Zhao
> **Workshop:** SmartLearn Days 2–3
> **Status:** Draft — ready for implementation

---

## User Stories

> Each story follows the format: *As a **[role]**, I want to **[action]**, so that **[benefit]**.*
> The three stories below form a natural learning workflow: encounter material → verify understanding → deepen knowledge.

### Story 1: Upload and ask (Entry point)

> As a **student preparing for an exam with a 60-page lecture PDF**, I want to **upload the file and ask questions in plain English**, so that **I can find answers without re-reading the entire document from start to finish**.

This is the core interaction. The student has limited time and a dense document. They need to jump directly to the information they care about. Without this, there is no product.

**Acceptance:** A student uploads a PDF, types "What are the three types of machine learning?", and receives an answer grounded in the lecture content within seconds.

### Story 2: Verify with page references (Trust)

> As a **student who received an AI-generated answer**, I want to **see the exact page number where each claim came from**, so that **I can open the original slide and verify the AI didn't hallucinate or cherry-pick information**.

This is the trust story. Without citations, the student cannot distinguish between an accurate answer and an AI confabulation. The page number is the bridge between the AI's summary and the original source — it turns the answer from "maybe true" into "checkable."

**Acceptance:** Every factual claim in the answer ends with `[Page X]`. The student navigates to that page in the PDF and confirms the information matches.

### Story 3: Follow-up conversation (Depth)

> As a **student who just read an answer about supervised learning**, I want to **ask a follow-up question like "can you give me an example?" without re-typing the entire context**, so that **I can deepen my understanding through natural back-and-forth dialogue**.

This is the depth story. Real studying is not a single Q&A — it's a conversation. The student starts broad ("what is supervised learning?"), then narrows ("what's an example?"), then challenges ("what are its limitations?"). Each question builds on the last. Without conversation context, every question feels like starting over.

**Acceptance:** The student asks three related questions in sequence. The third answer shows awareness of the earlier discussion without the student repeating the topic.

---

## Feature List

Features are ranked by priority. **P0 = Day 2 (must ship). P1 = Day 3 (completes the experience). P2 = Day 3 (if time allows).**

| Priority | Feature | Day | Rationale |
|----------|---------|-----|-----------|
| **P0** | PDF text extraction | Day 2 | The foundation. Nothing else works without text. Must handle text-based PDFs and gracefully explain when a PDF is scanned/image-only. |
| **P0** | LLM Q&A with page citation | Day 2 | The core feature. Upload a PDF, ask a question, get an answer where every claim cites its source page. This alone delivers the Stories 1 and 2. |
| **P1** | RAG pipeline (chunk → embed → search) | Day 3 | The scalability feature. Day 2 sends the entire PDF to the LLM, which breaks on anything longer than ~30 pages. RAG splits documents into chunks, embeds them as vectors, and retrieves only the relevant ones per question. This is what makes the tool work on real course materials. |
| **P1** | Web UI (React + FastAPI) | Day 3 | The accessibility feature. A command-line tool works for developers; a browser interface works for everyone. Upload a PDF via drag-and-drop, type questions in a chat box, see answers with formatted citations. |
| **P2** | Chat history / conversation memory | Day 3 | The continuity feature. Remembers previous questions and answers within a session so the student can have a natural conversation (Story 3). Without this, every question is standalone. |
| **P2** | Export answers as notes | Day 3 | The study-habit feature. After a Q&A session, the student can save all answers (with citations) as a Markdown or text file for later review. |

### Priority rationale

```
Day 2 ships the "does it work at all?" version:
  PDF in → text out → LLM call → cited answer.
  One question at a time. Command-line only. Small PDFs only.
  But: it proves the core value proposition (Story 1 + 2).

Day 3 ships the "would I actually use this?" version:
  RAG handles real-length PDFs. Web UI makes it accessible.
  Chat memory makes conversation natural.
  Export makes it a study tool, not a toy.
```

---

## What We Will NOT Build

Scope control is the hardest skill in product design. Every item below is something a reasonable person might want — but building any of them would consume Day 2's or Day 3's time budget without delivering core value. **Explicitly saying no is what keeps the project shippable.**

| We will NOT build | Why we're skipping it | What we'd need first |
|-------------------|----------------------|---------------------|
| **User authentication / login** | A login system needs password hashing, session tokens, a user database, registration flow, and password reset. That's a full Day of work that teaches web security — not AI-assisted learning. | A user base that needs private accounts. For a workshop demo, a single-user tool is enough. |
| **Multi-file / multi-PDF support** | Uploading one PDF and asking questions is already complex end-to-end. Adding multiple files introduces cross-document citation ("this claim is from file A page 3, file B page 7"), chunk deduplication, and a much more complex UI. | Perfect the single-PDF experience. Multi-file is a natural v2. |
| **Mobile app (iOS/Android)** | A mobile app requires either React Native (separate codebase) or a complete responsive redesign with touch-first interactions. The workshop builds one frontend — the web version. | The web UI working reliably. A responsive web app that works on mobile browsers is a cheaper first step. |
| **OCR for scanned PDFs** | Optical Character Recognition adds a heavy dependency (Tesseract), handles multiple languages poorly, and is slow. PDFs with selectable text cover 90% of course materials. | A clear user need for scanned documents. The current tool explains the limitation honestly (see PRD Done When #4). |
| **Real-time collaboration** | Multi-user editing of the same Q&A session needs WebSocket synchronization, conflict resolution, and presence indicators. It's a distributed systems problem, not an AI problem. | A single-user tool that works. |
| **Vector database beyond FAISS** | FAISS is an in-memory library perfect for a prototype. A production system might use Pinecone, Weaviate, or pgvector — but Day 3 barely has time to implement FAISS itself. | A prototype that proves RAG works. Swapping the vector store is a one-file change later. |

---

## Data Flow

### Day 2: Simple Mode (full-text)

On Day 2, the entire PDF text is sent to the LLM in a single prompt. This works for short documents but hits the context-window ceiling on anything beyond ~30 pages (roughly 30,000 words).

```
User uploads PDF (via CLI or web upload)
        │
        ▼
  [PDF parser: pdfplumber extracts text page by page]
        │
        ▼
      pages[]
        │  Each page labelled [Page 1], [Page 2], ...
        ▼
  [Build prompt: concatenate numbered pages + system instructions + user question]
        │
        ▼
      [LLM]
        │  OpenRouter: qwen/qwen3.5-flash-02-23
        ▼
  Answer with [Page X] citations
```

**Why this works (short PDFs):** The LLM sees all the text at once, so it can draw connections across pages. The page labels survive into the answer because the system prompt instructs the model to cite them.

**Why this fails (long PDFs):**
1. **Context window limit**: The LLM has a maximum input size (~128K tokens for qwen3.5-flash). A 200-page PDF can easily exceed this.
2. **Attention dilution**: Even if the text fits, the model's attention is spread across irrelevant content. The answer quality degrades.
3. **Cost**: Every API call sends the *entire* document, even if the question is about one paragraph.

### Day 3: RAG Mode (retrieval-augmented generation)

RAG changes the architecture from "send everything" to "find what's relevant, send only that." The key insight: **for any given question, 95% of the document is irrelevant — retrieve the 5% that matters.**

```
                     PDF UPLOAD
                         │
                         ▼
               [PDF parser: extract text]
                         │
                         ▼
                       pages
                         │
                         ▼
               [Split into chunks: ~500 characters each, with source page tracked]
                         │
                         ▼
             chunks[] with source_page metadata
                         │
                         ▼
               [Embed: turn each chunk into a numeric vector via embedding model]
                         │
                         ▼
                    embeddings[]
                         │
                         ▼
               [Vector store: FAISS index stores embeddings for fast search]
                         │
                         ║
                         ║  (upload done — now answering questions)
                         ║
                         ▼
                    USER QUESTION
                         │
                         ▼
               [Encode question: embed the question into the same vector space]
                         │
                         ▼
               [Similarity search: FAISS finds the top-K chunks closest to the question]
                         │
                         ▼
                  relevant chunks (e.g., top 3-5)
                         │
                         ▼
               [Build prompt: relevant chunks + system instructions + user question]
                         │
                         ▼
                       [LLM]
                         │
                         ▼
               Answer with [Page X] citations
```

**RAG in one picture (what the LLM sees):**

```
Traditional (Day 2):
┌──────────────────────────────────────────────────────┐
│  Entire 200-page PDF (80,000 words) ──────────> [LLM] │
│  "What is gradient descent?"                          │
│  → Answer: ...maybe? Context is drowning in noise.    │
└──────────────────────────────────────────────────────┘

RAG (Day 3):
┌──────────────────────────────────────────────────────┐
│  200-page PDF → chunks → embed → store (done once)    │
│                                                       │
│  "What is gradient descent?"                           │
│       → embed question                                │
│       → search FAISS                                  │
│       → retrieve top 3 chunks (1500 chars total)      │
│       → send only those 3 chunks to [LLM]             │
│  → Answer: "Gradient descent is an optimization       │
│     algorithm that... [Page 42, Page 47]"             │
│  (Precise, fast, cheap — and fits in context)         │
└──────────────────────────────────────────────────────┘
```

**Why this is better:**
1. **Scales to any document length**: The vector store handles millions of chunks.
2. **Higher answer quality**: The LLM sees only the most relevant context, so its attention is focused.
3. **Cheaper API calls**: Send 1,500 characters instead of 80,000 — that's a 98% token reduction.
4. **Source tracking survives**: Each chunk carries its source page, so citations still work.

### Component map: from data flow to code

| Data flow step | Day 2 implementation | Day 3 implementation |
|---------------|---------------------|---------------------|
| PDF parser | `pdfplumber` (done in Section 4) | Same — reuse `pdf_summary.py` extraction logic |
| Chunk text | Not needed | Custom splitter: break at paragraph boundaries, ~500 chars per chunk |
| Embed | Not needed | OpenRouter embedding endpoint (or sentence-transformers locally) |
| Vector store | Not needed | FAISS `IndexFlatL2` — in-memory, no server, one import |
| Build prompt | `cli_qa.py`-style numbered text | Same format, but text comes from search results, not the whole PDF |
| LLM call | `openai` SDK → OpenRouter | Same pattern — the API call doesn't change, only the input does |
| Web UI | Not applicable | React file upload → FastAPI `/upload` + `/ask` endpoints |

---

## Architecture Sketch: Day 3 Web App

This is a preview — the exact implementation will be designed on Day 3. The goal here is to see how the data flow maps to actual components.

```
┌─────────────────────┐       HTTP/JSON       ┌─────────────────────┐
│   React Frontend    │ ◄──────────────────► │   FastAPI Backend    │
│                     │                       │                      │
│  • File drop zone   │  POST /upload (PDF)   │  • PDF parser        │
│  • Chat interface   │  POST /ask (question)  │  • Chunk splitter    │
│  • Answer display   │                       │  • Embedding client  │
│  • Page citations   │                       │  • FAISS index       │
│                     │                       │  • OpenRouter client │
└─────────────────────┘                       └─────────────────────┘
```

**API endpoints (draft):**

| Method | Path | Input | Output | Notes |
|--------|------|-------|--------|-------|
| `POST` | `/upload` | PDF file (multipart) | `{doc_id, page_count}` | Parse PDF, chunk, embed, store in FAISS |
| `POST` | `/ask` | `{doc_id, question}` | `{answer, citations: [{text, page}]}` | Embed question, search FAISS, call LLM |
| `GET` | `/health` | — | `{status: "ok"}` | Liveness check |

---

## Day 2 ↔ Day 3 Progression

| Dimension | Day 2 | Day 3 |
|-----------|-------|-------|
| **Interface** | Command line (`python3 pdf_summary.py`) | Web browser (React chat UI) |
| **PDF size limit** | ~30 pages (context window) | Unlimited (RAG retrieves relevant chunks) |
| **Question scope** | One question, fresh context each time | Multi-turn conversation with memory |
| **Answer quality** | Good for short docs, degrades with length | Consistent regardless of document length |
| **What the student learns** | LLM API basics, prompt design, PDF extraction | RAG architecture, web app structure, vector search |
