from apscheduler.schedulers.background import BackgroundScheduler

from backend.crawler.crawler import WebCrawler
from backend.extractor.extractor import HTMLExtractor
from backend.processing.chunker import TextChunker
from backend.processing.embedder import Embedder
from backend.vectorstore.vectordb import VectorDB
from backend.freshness.freshness import (
    process_page,
    get_active_crawl_sources,
    mark_source_crawled,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def scheduled_crawl():
    """
    Recrawl the actual saved seed URLs from the database.
    Preserves section-level metadata instead of flattening everything.
    """
    logger.info("Scheduled incremental crawl started")

    sources = get_active_crawl_sources()
    if not sources:
        logger.info("No active crawl sources found. Scheduler skipped.")
        return

    extractor = HTMLExtractor()
    chunker = TextChunker()
    embedder = Embedder()
    vectordb = VectorDB()

    total_pages = 0
    total_sections_updated = 0

    for source in sources:
        seed_url = source["seed_url"]
        max_depth = source["max_depth"]
        max_pages = source["max_pages"]

        logger.info(
            f"Scheduled crawl for seed_url={seed_url}, "
            f"max_depth={max_depth}, max_pages={max_pages}"
        )

        try:
            crawler = WebCrawler(
                seed_urls=[seed_url],
                max_pages=max_pages,
                max_depth=max_depth,
            )

            pages = crawler.crawl()
            total_pages += len(pages)

            for page in pages:
                extracted = extractor.extract(
                    url=page["url"],
                    html=page["html"],
                    headers=page["headers"],
                )

                if not extracted:
                    continue

                title = extracted.get("title", "")

                # IMPORTANT:
                # process section by section, preserving section metadata
                for sec in extracted.get("sections", []):
                    section_name = (sec.get("section") or "General").strip()
                    section_content = (sec.get("content") or "").strip()

                    if not section_content:
                        continue

                    metadata = {
                        "title": title,
                        "section": section_name,
                    }

                    updated = process_page(
                        url=page["url"],
                        clean_text=section_content,
                        metadata=metadata,
                        vectordb=vectordb,
                        chunker=chunker,
                        embedder=embedder,
                    )

                    if updated:
                        total_sections_updated += 1

            mark_source_crawled(seed_url)

        except Exception as e:
            logger.exception(f"Scheduled crawl failed for {seed_url}: {e}")

    logger.info(
        f"Scheduled crawl completed. pages_seen={total_pages}, "
        f"sections_updated={total_sections_updated}"
    )


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        scheduled_crawl,
        trigger="interval",
        hours=24,
        id="incremental_crawl_job",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started. Incremental crawl runs every 24 hours.")