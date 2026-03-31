# Enterprise Policy Q&A Assistant

> A locally-deployed, hallucination-controlled intelligent Q&A system built on Retrieval Augmented Generation (RAG) for university policy documents.

---

## What It Does

Ask a question in plain English. Get a precise, cited answer pulled directly from official policy documents — with the source document name, page number, and a confidence score. If the answer is not in the documents, the system explicitly refuses rather than guessing.

```
User:    "Can students share their passwords?"
System:  "Users are strictly prohibited from sharing passwords with anyone,
          including supervisors and IT staff."
          Source: Regent University AUP (Page 5) | Confidence: 0.74 | GROUNDED ✓
```

---

## Key Features

- **No hallucinations** — two independent safety gates block unverified answers
- **Full citations** — every answer includes source document and page number
- **Three-agent pipeline** — intent classification, query rewriting, answer validation
- **Two-stage retrieval** — ANN vector search + cross-encoder neural reranking
- **Provider toggle** — switch between local Ollama and Groq API in one config line
- **Auto index building** — builds ChromaDB index on first launch, loads instantly after
- **Fully local option** — entire pipeline runs on your machine with zero cloud calls
- **Light professional UI** — Streamlit web interface with confidence scoring

---

## System Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  Agent 1 — Intent Classifier │  Rule-based keyword matching
│  POLICY / GREETING / OOB    │  < 1ms — no LLM call
└──────────────┬──────────────┘
               │ POLICY only
               ▼
┌─────────────────────────────┐
│  Agent 2 — Query Rewriter   │  Regex pattern replacement
│  Informal → Formal language │  < 1ms — no LLM call
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  Embedding                  │  mxbai-embed-large (Ollama)
│  Query → 1024-dim vector    │  ~500ms
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  ChromaDB ANN Search        │  HNSW graph — cosine distance
│  Returns top K=6 chunks     │  ~10ms
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  Cross-Encoder Reranker     │  ms-marco-MiniLM-L-6-v2
│  Re-scores (query, chunk)   │  ~1,500ms
│  pairs → picks best 3       │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  Distance Threshold Gate    │  distance > 0.8 → REFUSED
│  Blocks irrelevant topics   │  < 1ms
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  LLM Answer Generation      │  llama3 (Ollama) or
│  Strict grounding prompt    │  LLaMA 3.1 8B (Groq API)
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  Agent 3 — Validator        │  Token overlap scoring
│  GROUNDED / HALLUCINATED    │  < 1ms — no LLM call
└──────────────┬──────────────┘
               ▼
     Answer + Citation + Confidence Score
```

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Web UI |
| LLM (local) | llama3 via Ollama | Answer generation |
| LLM (fast) | LLaMA 3.1 8B via Groq API | Answer generation |
| Embeddings | mxbai-embed-large (Ollama) | Text → vectors |
| Vector DB | ChromaDB (HNSW) | ANN search |
| Reranker | ms-marco-MiniLM-L-6-v2 | Neural reranking |
| PDF Loading | LangChain PyPDFLoader | Document ingestion |
| Chunking | LangChain RecursiveCharacterTextSplitter | Text splitting |
| Prompt | LangChain ChatPromptTemplate | LLM prompt formatting |
| Env Secrets | python-dotenv | API key management |

---

## ML & Search Techniques

| Technique | Where | Description |
|---|---|---|
| Dense Vector Embedding | embedder.py | Converts text to high-dimensional semantic vectors |
| ANN — HNSW | ChromaDB (internal) | Approximate Nearest Neighbor graph search |
| Cosine Distance | ChromaDB metric | Measures semantic similarity between vectors |
| Two-Stage Retrieval | Full pipeline | Fast ANN (top 6) → precise rerank (top 3) |
| Cross-Encoder Reranking | retriever.py | Neural model reads query+chunk together |
| RAG | rag.py | Retrieval Augmented Generation architecture |
| Sliding Window Chunking | chunker.py | 600-char chunks with 120-char overlap |
| Token Overlap (ROUGE-like) | validator_agent.py | Hallucination detection via lexical overlap |
| Rule-Based NLP | intent + rewriter agents | Keyword sets and regex — deterministic, fast |

---

## Document Corpus

9 university policy PDFs indexed across multiple institutions and policy types:

| Document | Organisation | Type |
|---|---|---|
| Acceptable Use Policy | Illinois Tech | IT Security |
| Acceptable Use — University Computers | Radford University | IT Policy |
| Acceptable Use Policy | Univ. of Virgin Islands | Acceptable Use |
| Computer Usage Policy | Fairleigh Dickinson | Computer Use |
| IT Acceptable Use Policy | SUNY Optometry | IT Security |
| Individual Financial Conflict of Interest | Univ. of Utah | Research Compliance |
| Firearms on Campus Policy | Univ. of Utah | Campus Safety |
| Acceptable Use Policy | Regent University | IT Security |
| Acceptable Use Policy | Mount Saint Mary's | IT Policy |

---

## Project Structure

```
project/
├── app.py                    # Streamlit UI — main entry point
├── main.py                   # Terminal entry point (CLI)
├── .env                      # API keys (never commit this)
├── .gitignore
├── README.md
│
├── data/                     # Place all PDF documents here
│   ├── Acceptable-Use-Policy.pdf
│   └── ...
│
├── vector_db/                # ChromaDB persistent store (auto-created)
│
└── src/
    ├── config.py             # All configuration in one place
    ├── loader.py             # PDF loading
    ├── chunker.py            # Text splitting
    ├── embedder.py           # Embedding + ChromaDB indexing
    ├── retriever.py          # ANN search + cross-encoder reranking
    ├── rag.py                # Full RAG pipeline orchestration
    ├── llm.py                # LLM connection (Ollama or Groq)
    ├── logger.py             # Centralised logging
    ├── intent_agent.py       # Agent 1 — intent classification
    ├── rewriter_agent.py     # Agent 2 — query rewriting
    └── validator_agent.py    # Agent 3 — answer validation
```

---

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### Step 1 — Clone and install dependencies

```bash
pip install streamlit langchain langchain-community langchain-ollama \
            chromadb sentence-transformers langchain-groq python-dotenv
```

### Step 2 — Pull local models (for Ollama mode)

```bash
ollama pull llama3
ollama pull mxbai-embed-large
```

### Step 3 — Add your PDF documents

Place all policy PDF files into the `data/` folder.

### Step 4 — Configure environment

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com)

### Step 5 — Configure provider

Open `src/config.py` and set your preferred LLM provider:

```python
# For Groq (fast — recommended)
LLM_PROVIDER = "groq"
LLM_MODEL    = "llama-3.1-8b-instant"

# For Ollama (local/private)
LLM_PROVIDER = "ollama"
LLM_MODEL    = "llama3"
```

---

## Running the App

```bash
# Web UI
streamlit run app.py

# Terminal / CLI
python main.py
```

On **first launch**, the system automatically builds the ChromaDB index from your PDFs. This takes a few minutes depending on document count. Every subsequent launch loads the existing index instantly.

---

## Configuration Reference

All parameters are in `src/config.py`:

```python
# Chunking
CHUNK_SIZE          = 600     # characters per chunk
CHUNK_OVERLAP       = 120     # overlap between chunks

# Models
EMBEDDING_MODEL     = "mxbai-embed-large"
RERANKER_MODEL      = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_PROVIDER        = "groq"                    # "groq" or "ollama"
LLM_MODEL           = "llama-3.1-8b-instant"   # see table below

# Retrieval
RETRIEVAL_K         = 6       # chunks fetched from ChromaDB
RERANKER_TOP_N      = 3       # chunks sent to LLM after reranking
RELEVANCE_THRESHOLD = 0.8     # max cosine distance before refusing
```

### Available LLM Models

| Provider | Model String | Speed | Quality |
|---|---|---|---|
| Groq | `llama-3.1-8b-instant` | ~0.5s | Good |
| Groq | `llama3-70b-8192` | ~2s | Excellent |
| Groq | `mixtral-8x7b-32768` | ~1s | Very Good |
| Ollama | `llama3` | ~12s | Good |

---

## How the Three Agents Work

### Agent 1 — Intent Classifier
Classifies every query before touching the RAG pipeline. Non-policy queries are handled instantly without any retrieval.

| Intent | Example | Action |
|---|---|---|
| `POLICY` | "Can I install software?" | Proceeds to RAG |
| `GREETING` | "Hello", "Thanks" | Returns pre-written response |
| `OUT_OF_SCOPE` | "What's the weather?" | Returns redirect message |
| `UNCLEAR` | "what" | Asks user to rephrase |

### Agent 2 — Query Rewriter
Converts informal language to formal policy terminology before embedding — improves retrieval accuracy significantly.

```
"can i share my password"
→ "Are users permitted to disclose authentication credentials"

"what if i get caught?"
→ "What are the consequences if found in violation"
```

### Agent 3 — Answer Validator
Measures token overlap between the generated answer and the retrieved context. Blocks answers that are not grounded in the source documents.

| Verdict | Overlap | Action |
|---|---|---|
| `GROUNDED` | ≥ 45% | Answer served |
| `PARTIAL` | 25–45% | Answer served |
| `HALLUCINATED` | < 25% | Answer blocked — REFUSED |

---

## Performance

| Stage | Old (4 LLM calls) | Ollama Local | Groq API |
|---|---|---|---|
| Agent 1 — Intent | ~10s | < 1ms | < 1ms |
| Agent 2 — Rewriter | ~10s | < 1ms | < 1ms |
| Embedding | ~500ms | ~500ms | ~500ms |
| ChromaDB Search | ~10ms | ~10ms | ~10ms |
| Cross-Encoder Rerank | ~1,500ms | ~1,500ms | ~1,500ms |
| LLM Generation | ~12,000ms | ~12,000ms | ~500ms |
| Agent 3 — Validator | ~10s | < 1ms | < 1ms |
| **Total** | **~42–50s** | **~14–15s** | **~2.5–3s** |

---

## Adding New Documents

1. Place the new PDF in the `data/` folder
2. Add an entry to `POLICY_REGISTRY` in `app.py`:

```python
"your_new_policy.pdf": {
    "label":   "Your Policy Name",
    "type":    "Policy Type",
    "version": "v1.0",
    "date":    "Jan 2025",
    "dept":    "Department",
    "org":     "Organisation Name",
    "scope":   "All Users",
},
```

3. Click the **⟳ Rebuild** button in the sidebar

---

## Security

| Aspect | Status | Detail |
|---|---|---|
| Data Privacy (Ollama) |  Strong | Zero data leaves machine |
| Data Privacy (Groq) |  Note | Top 3 retrieved chunks sent to Groq per query |
| Hallucination Control |  Strong | Distance gate + token overlap validator |
| Prompt Injection | Partial | Intent classifier + strict grounding prompt |
| API Key Safety | Strong | Stored in .env — never in source code |

> **Important:** Never commit your `.env` file to version control. Add it to `.gitignore`.

---

## .gitignore

```
.env
vector_db/
__pycache__/
*.pyc
.DS_Store
```

---

## Logs

The system logs every query with full pipeline detail to the `logs/` folder:

```
BEFORE RERANKING — ChromaDB raw order (by cosine distance)
  Pos  Distance  Source
  1      0.4812  regent_uni_aup.pdf p.5
  2      0.5023  Acceptable-Use-Policy.pdf p.3
  ...

AFTER RERANKING — Cross-encoder order (by relevance score)
  Pos  RerankScore  Distance  Status        Source
  1        4.8821    0.5023   >>> TO LLM    Acceptable-Use-Policy.pdf p.3
  2        3.2104    0.4812   >>> TO LLM    regent_uni_aup.pdf p.5
  ...
```

---

## LangChain Usage

LangChain is used **only** as a utility library in four places. The agent pipeline, retrieval orchestration, and reranking are all custom Python.

| File | LangChain Component | Purpose |
|---|---|---|
| loader.py | PyPDFLoader | Read PDFs into Document objects |
| chunker.py | RecursiveCharacterTextSplitter | Split text into chunks |
| embedder.py | OllamaEmbeddings | Convert text to vectors |
| llm.py / rag.py | ChatOllama / ChatGroq / ChatPromptTemplate | LLM connection and prompt |

---

## Future Improvements

- [ ] **Hybrid Search** — BM25 + dense vector search with RRF fusion
- [ ] **Multi-turn conversation** — maintain context across follow-up questions
- [ ] **User feedback loop** — rate answers to improve retrieval over time
- [ ] **Role-based access** — filter policies by user role
- [ ] **Authentication layer** — password gate for deployment
- [ ] **Sentence window chunking** — retrieve surrounding context for better answers
- [ ] **Analytics dashboard** — track query patterns and refusal rates

---

## Architecture Notes

**Why ChromaDB over FAISS?**
At ~800 chunks, the 7ms speed difference is irrelevant. ChromaDB's built-in metadata handling (source filename, page number) saves significant complexity. FAISS would only be worth it at 100k+ chunks.

**Why rule-based agents over LLM agents?**
The domain intents are highly predictable. Rules are as accurate as LLM classification for this use case and eliminate 3 sequential LLM calls — reducing query time by 70%.

**Why cross-encoder reranker?**
Cosine distance compares vectors independently. The cross-encoder reads query and chunk together, understanding their interaction. It frequently promotes chunks that were ranked 2nd or 3rd by ChromaDB to position 1 — the most relevant chunk for the actual question.

**Why threshold gate after reranking?**
The reranker picks the best from what ChromaDB returned. But if everything ChromaDB returned is irrelevant (topic not in documents), the threshold catches it and refuses rather than serving a hallucinated answer.

---

## License

This project was developed as a Capstone I academic project.

---

*Built with LangChain · ChromaDB · Ollama · Groq · Streamlit · Sentence Transformers*
