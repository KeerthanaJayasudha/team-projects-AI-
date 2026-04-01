from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import uuid

from backend.crawler.crawler import WebCrawler
from backend.extractor.extractor import HTMLExtractor
from backend.processing.chunker import TextChunker
from backend.processing.embedder import Embedder
from backend.vectorstore.vectordb import VectorDB
from backend.freshness.freshness import (
    process_page,
    register_crawl_sources,
    clear_freshness_records,
    create_crawl_session,
    complete_crawl_session,
    fail_crawl_session,
)
from backend.freshness.scheduler import start_scheduler
from backend.rag.rag_pipeline import RAGPipeline
from backend.evaluation.evaluation import evaluate_query
from backend.utils.logger import get_logger
from backend.utils.config import LLM_MODEL, TOP_K

logger = get_logger(__name__)

app = FastAPI(title="URL-Based RAG Assistant (Ollama Powered)")

vectordb = VectorDB()
embedder = Embedder()
extractor = HTMLExtractor()
chunker = TextChunker()

rag_pipeline = RAGPipeline(
    vectordb=vectordb,
    embedder=embedder,
    model_name=LLM_MODEL
)

CURRENT_CRAWL_ID = None


@app.on_event("startup")
def start_background_tasks():
    try:
        start_scheduler()
        logger.info("Background scheduler started successfully")
    except Exception:
        logger.exception("Failed to start background scheduler")


class CrawlRequest(BaseModel):
    urls: List[str] = Field(..., example=["https://example.com"])
    max_depth: int = Field(2, ge=0, le=5)
    max_pages: int = Field(20, ge=1, le=200)
    update_strategy: str = Field("incremental", pattern="^(incremental|force)$")


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(TOP_K, ge=1, le=20)
    search_scope: Literal["latest", "all"] = "latest"


@app.get("/status")
def status():
    try:
        logger.info("Status endpoint called")
        return {
            "status": "running",
            "documents_indexed": vectordb.count(),
            "current_crawl_id": CURRENT_CRAWL_ID,
            "llm_model": LLM_MODEL
        }
    except Exception as e:
        logger.exception(f"STATUS ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch system status")


def build_query_filter(search_scope: str) -> Optional[Dict[str, Any]]:
    if search_scope == "latest":
        if not CURRENT_CRAWL_ID:
            raise HTTPException(
                status_code=400,
                detail="No active crawl found. Please crawl URLs first."
            )
        return {"crawl_id": CURRENT_CRAWL_ID}

    if search_scope == "all":
        return None

    raise HTTPException(status_code=400, detail="Invalid search_scope value")


@app.post("/crawl")
def crawl(request: CrawlRequest):
    global CURRENT_CRAWL_ID

    crawl_id = str(uuid.uuid4())
    CURRENT_CRAWL_ID = crawl_id

    try:
        cleaned_urls = [url.strip() for url in request.urls if url and url.strip()]
        if not cleaned_urls:
            raise HTTPException(status_code=400, detail="No valid URLs provided")

        logger.info(f"Starting crawl for URLs: {cleaned_urls}")
        logger.info(f"Current crawl id: {crawl_id}")

        register_crawl_sources(
            seed_urls=cleaned_urls,
            max_depth=request.max_depth,
            max_pages=request.max_pages
        )

        create_crawl_session(
            crawl_id=crawl_id,
            seed_urls=cleaned_urls,
            update_strategy=request.update_strategy
        )

        if request.update_strategy == "force":
            vectordb.clear()
            clear_freshness_records(cleaned_urls)
            logger.info("Force update selected — vector database and freshness metadata cleared")
        else:
            logger.info("Incremental update selected — existing vectors preserved")

        crawler = WebCrawler(
            seed_urls=cleaned_urls,
            max_pages=request.max_pages,
            max_depth=request.max_depth
        )

        pages = crawler.crawl()
        logger.info(f"Total pages discovered: {len(pages)}")

        sections_updated = 0
        total_sections_seen = 0
        pages_processed = 0

        for page in pages:
            if not page.get("html"):
                continue

            pages_processed += 1
            logger.info(f"Processing page: {page['url']}")

            extracted = extractor.extract(
                url=page["url"],
                html=page["html"],
                headers=page.get("headers", {}),
                crawl_id=crawl_id
            )

            if not extracted or not extracted.get("sections"):
                logger.warning(f"No content extracted for {page['url']}")
                continue

            logger.info(
                f"Extracted sections from {page['url']}: {len(extracted['sections'])}"
            )

            for sec in extracted["sections"]:
                section_title = str(sec.get("section", "General")).strip() or "General"
                section_content = str(sec.get("content", "")).strip()

                if not section_content:
                    continue

                total_sections_seen += 1

                metadata = {
                    "title": str(extracted.get("title", "")),
                    "url": str(page["url"]),
                    "section": section_title,
                    "crawl_id": crawl_id,
                }

                updated = process_page(
                    url=page["url"],
                    clean_text=section_content,
                    metadata=metadata,
                    vectordb=vectordb,
                    chunker=chunker,
                    embedder=embedder
                )

                if updated:
                    sections_updated += 1
                    logger.info(f"Indexed section '{section_title}' from {page['url']}")

        documents_indexed = vectordb.count()

        complete_crawl_session(
            crawl_id=crawl_id,
            pages_crawled=len(pages),
            pages_processed=pages_processed,
            sections_seen=total_sections_seen,
            sections_updated=sections_updated,
            documents_indexed=documents_indexed,
            status="completed",
        )

        logger.info(
            f"Crawl completed | pages_crawled={len(pages)} | "
            f"pages_processed={pages_processed} | sections_updated={sections_updated} | "
            f"documents_indexed={documents_indexed}"
        )

        return {
            "status": "success",
            "pages_crawled": len(pages),
            "pages_processed": pages_processed,
            "sections_updated": sections_updated,
            "total_sections_seen": total_sections_seen,
            "documents_indexed": documents_indexed,
            "update_strategy": request.update_strategy,
            "crawl_id": crawl_id
        }

    except HTTPException as e:
        fail_crawl_session(crawl_id, e.detail)
        raise
    except Exception as e:
        logger.exception(f"CRAWL ERROR: {e}")
        fail_crawl_session(crawl_id, str(e))
        raise HTTPException(status_code=500, detail="Internal error occurred during crawl")


@app.post("/query")
def query(request: QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        where_filter = build_query_filter(request.search_scope)

        logger.info(f"User question: {request.question}")
        logger.info(f"Search scope: {request.search_scope} | where={where_filter}")

        response = rag_pipeline.answer(
            question=request.question,
            top_k=request.top_k,
            where=where_filter
        )

        response["search_scope"] = request.search_scope
        response["llm_model"] = LLM_MODEL
        logger.info("Answer generated successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"QUERY ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal error occurred during query")


@app.post("/evaluate")
def evaluate(request: QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        where_filter = build_query_filter(request.search_scope)

        retrieved = rag_pipeline.retrieve(
            request.question,
            request.top_k,
            where=where_filter
        )

        if not retrieved:
            return {
                "question": request.question,
                "search_scope": request.search_scope,
                "precision@k": 0.0,
                "recall@k": 0.0
            }

        metrics = evaluate_query(
            retrieved_chunks=retrieved,
            k=request.top_k,
            threshold=0.30
        )

        result = {
            "question": request.question,
            "search_scope": request.search_scope,
            **metrics
        }

        logger.info(
            f"Evaluation completed | question='{request.question}' | result={result}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"EVALUATION ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal error occurred during evaluation")


@app.get("/debug/chunks")
def debug_chunks(limit: int = 20, search_scope: Literal["latest", "all"] = "latest"):
    try:
        where_filter = build_query_filter(search_scope)
        rows = vectordb.get_chunk_samples(limit=limit, where=where_filter)
        return {
            "search_scope": search_scope,
            "count": len(rows),
            "chunks": rows
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"DEBUG CHUNKS ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chunk samples")