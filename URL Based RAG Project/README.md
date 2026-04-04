# URL-Based RAG – Live Website Knowledge Assistant

## Objective

Build a Retrieval-Augmented Generation (RAG) system that answers questions from live website content ingested via URLs.

## System Architecture

User URL  
→ Crawler  
→ HTML Cleaner  
→ Chunking  
→ Embedding (Sentence Transformers)  
→ ChromaDB  
→ Retrieval  
→ Answer Generation  

## Website Crawling

The crawler automatically explores websites starting from one or more seed URLs.

Features:
Multi-URL crawling
Depth-controlled crawling
Duplicate URL removal
Domain restriction
Robots.txt compliance

## HTML Cleaning & Boilerplate Removal

The system removes navigation bars, advertisements, scripts, footers, sidebars using:
BeautifulSoup tag filtering
CSS class filtering
Trafilatura content extraction 

## Metadata Handling

Each text chunk stores metadata like URL, page title, section heading, crawl time, and content hash.

## Token-Based Text Chunking

Large documents are split into overlapping token chunks for better retrieval performance.

## Embeddings

The system converts text chunks into semantic vectors using sentence-transformers/all-MiniLM-L6-v2.

## Vector Database

The embeddings are stored in ChromaDB, a persistent vector database.

## Retrieval-Augmented Generation (RAG)

User asks a question
Query is converted to embedding
Top-K relevant chunks are retrieved
Chunks are sent to the LLM
The LLM generates an answer grounded in retrieved context

## Freshness Strategy

Crawl webpage
Generate content hash
Compare with stored hash
 If changed:
   --> delete old vectors
   --> re-chunk content
   --> regenerate embeddings
   --> store updated vectors

## Scheduled Re-Crawling

The system automatically checks for updates using a APScheduler.
This keeps the knowledge base continuously refreshed.

## Backend API (FastAPI)

Crawl Websites -> Post\crawl
Query system -> Post\Query
System Status -> GET\Status
Retrieval Evaluation -> POST /evaluate

## Frontend (Streamlit)

Multiple URL input fields
Add/Remove URL functionality
Crawl progress indicator
Question input box
Answer display
Source references
Retrieval evaluation metrics

## How to Run

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
ollama serve
python -m uvicorn backend.main:app
streamlit run frontend/app.py
