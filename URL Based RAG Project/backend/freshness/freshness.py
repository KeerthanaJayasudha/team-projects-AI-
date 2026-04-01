import hashlib
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import or_

from backend.database.db import SessionLocal, init_db
from backend.database.models import PageHash, CrawlSource, CrawlSession
from backend.utils.logger import get_logger

logger = get_logger(__name__)

init_db()


def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _utc_now():
    return datetime.utcnow()


def register_crawl_sources(
    seed_urls: List[str],
    max_depth: int,
    max_pages: int,
) -> None:
    if not seed_urls:
        return

    session = SessionLocal()
    now = _utc_now()

    try:
        unique_urls = []
        seen = set()

        for url in seed_urls:
            cleaned = (url or "").strip()
            if cleaned and cleaned not in seen:
                unique_urls.append(cleaned)
                seen.add(cleaned)

        for url in unique_urls:
            existing = session.query(CrawlSource).filter_by(seed_url=url).first()

            if existing:
                existing.max_depth = max_depth
                existing.max_pages = max_pages
                existing.is_active = True
                existing.updated_at = now
            else:
                session.add(
                    CrawlSource(
                        seed_url=url,
                        max_depth=max_depth,
                        max_pages=max_pages,
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                        last_crawled=None,
                    )
                )

        session.commit()
        logger.info(f"Registered {len(unique_urls)} crawl source(s)")

    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to register crawl sources: {e}")
        raise
    finally:
        session.close()


def get_active_crawl_sources() -> List[Dict]:
    session = SessionLocal()

    try:
        rows = session.query(CrawlSource).filter_by(is_active=True).all()

        return [
            {
                "seed_url": row.seed_url,
                "max_depth": row.max_depth,
                "max_pages": row.max_pages,
                "last_crawled": row.last_crawled,
                "source_id": row.id,
            }
            for row in rows
        ]
    except Exception as e:
        logger.exception(f"Failed to load active crawl sources: {e}")
        return []
    finally:
        session.close()


def mark_source_crawled(seed_url: str) -> None:
    session = SessionLocal()
    now = _utc_now()

    try:
        row = session.query(CrawlSource).filter_by(seed_url=seed_url).first()
        if row:
            row.last_crawled = now
            row.updated_at = now
            session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to mark source crawled for {seed_url}: {e}")
    finally:
        session.close()


def create_crawl_session(
    crawl_id: str,
    seed_urls: List[str],
    update_strategy: str,
) -> None:
    session = SessionLocal()
    now = _utc_now()

    try:
        source_id = None
        if seed_urls:
            first_url = seed_urls[0]
            source = session.query(CrawlSource).filter_by(seed_url=first_url).first()
            if source:
                source_id = source.id

        existing = session.query(CrawlSession).filter_by(crawl_id=crawl_id).first()
        if existing:
            return

        session.add(
            CrawlSession(
                crawl_id=crawl_id,
                source_id=source_id,
                update_strategy=update_strategy,
                status="started",
                started_at=now,
            )
        )
        session.commit()
        logger.info(f"Created crawl session: {crawl_id}")

    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to create crawl session {crawl_id}: {e}")
        raise
    finally:
        session.close()


def complete_crawl_session(
    crawl_id: str,
    pages_crawled: int,
    pages_processed: int,
    sections_seen: int,
    sections_updated: int,
    documents_indexed: int,
    status: str = "completed",
    error_message: Optional[str] = None,
) -> None:
    session = SessionLocal()
    now = _utc_now()

    try:
        row = session.query(CrawlSession).filter_by(crawl_id=crawl_id).first()
        if not row:
            logger.warning(f"Crawl session not found for completion: {crawl_id}")
            return

        row.completed_at = now
        row.status = status
        row.pages_crawled = pages_crawled
        row.pages_processed = pages_processed
        row.sections_seen = sections_seen
        row.sections_updated = sections_updated
        row.documents_indexed = documents_indexed
        row.error_message = error_message

        session.commit()
        logger.info(f"Completed crawl session: {crawl_id}")

    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to complete crawl session {crawl_id}: {e}")
    finally:
        session.close()


def fail_crawl_session(crawl_id: str, error_message: str) -> None:
    session = SessionLocal()
    now = _utc_now()

    try:
        row = session.query(CrawlSession).filter_by(crawl_id=crawl_id).first()
        if row:
            row.status = "failed"
            row.completed_at = now
            row.error_message = error_message
            session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to mark crawl session failed {crawl_id}: {e}")
    finally:
        session.close()


def clear_freshness_records(urls: Optional[List[str]] = None) -> None:
    session = SessionLocal()

    try:
        if not urls:
            deleted = session.query(PageHash).delete()
            session.commit()
            logger.info(f"Cleared all freshness records: {deleted}")
            return

        total_deleted = 0
        for url in urls:
            deleted = (
                session.query(PageHash)
                .filter(
                    or_(
                        PageHash.url == url,
                        PageHash.url.like(f"{url}::%"),
                    )
                )
                .delete(synchronize_session=False)
            )
            total_deleted += deleted

        session.commit()
        logger.info(f"Cleared {total_deleted} freshness record(s)")

    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to clear freshness records: {e}")
        raise
    finally:
        session.close()


def deactivate_missing_sources(active_seed_urls: List[str]) -> None:
    session = SessionLocal()
    now = _utc_now()

    try:
        active_set = {u.strip() for u in active_seed_urls if u and u.strip()}
        rows = session.query(CrawlSource).all()

        for row in rows:
            row.is_active = row.seed_url in active_set
            row.updated_at = now

        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to deactivate missing sources: {e}")
        raise
    finally:
        session.close()


def process_page(
    url: str,
    clean_text: str,
    metadata: dict,
    vectordb,
    chunker,
    embedder,
) -> bool:
    session = SessionLocal()
    now = _utc_now()

    try:
        section = (metadata.get("section") or "General").strip()
        title = (metadata.get("title") or "").strip()
        crawl_id = metadata.get("crawl_id")

        url_section_key = f"{url}::{section}"

        if not clean_text or not clean_text.strip():
            logger.warning(f"Empty content for {url_section_key}")
            return False

        new_hash = generate_hash(clean_text)
        existing = session.query(PageHash).filter_by(url=url_section_key).first()

        if existing and existing.content_hash == new_hash:
            existing.last_checked = now
            if crawl_id:
                existing.crawl_id = crawl_id
            session.commit()
            logger.info(f"No change detected for {url_section_key}")
            return False

        logger.info(f"Content change detected for {url_section_key}. Re-indexing")

        vectordb.delete_by_url_section(url, section)

        chunks = chunker.chunk_text(clean_text)
        if not chunks:
            logger.warning(f"No chunks generated for {url_section_key}")
            return False

        embeddings = embedder.embed_documents(chunks)
        if not embeddings:
            logger.error(f"Embedding generation failed for {url_section_key}")
            return False

        metadata_list = []
        ids = []

        safe_section = section.replace("/", "_").replace("\\", "_").strip()
        safe_url = url.replace("/", "_").replace("\\", "_").replace(":", "_")

        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "url": url,
                "title": title,
                "section": section,
                "chunk_index": i,
                "crawl_timestamp": now.isoformat(),
                "content_hash": new_hash,
            }
            metadata_list.append(chunk_metadata)
            ids.append(f"{safe_url}::{safe_section}::{i}")

        vectordb.add_documents(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadata_list,
            ids=ids,
        )

        if existing:
            existing.content_hash = new_hash
            existing.last_checked = now
            existing.last_updated = now
            if crawl_id:
                existing.crawl_id = crawl_id
        else:
            session.add(
                PageHash(
                    url=url_section_key,
                    content_hash=new_hash,
                    last_checked=now,
                    last_updated=now,
                    crawl_id=crawl_id,
                )
            )

        session.commit()
        logger.info(f"Re-indexing completed for {url_section_key}")
        return True

    except Exception as e:
        session.rollback()
        logger.exception(f"Failed processing page freshness for {url}: {e}")
        return False
    finally:
        session.close()