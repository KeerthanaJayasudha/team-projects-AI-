import re
import hashlib
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
import trafilatura

from backend.database.db import SessionLocal
from backend.database.models import PageMetadata, CrawlSession
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class HTMLExtractor:
    def extract(
        self,
        url: str,
        html: str,
        headers: dict,
        crawl_id: Optional[str] = None,
        crawl_session_id: Optional[int] = None
    ):
        """
        Clean HTML and extract structured sections.

        Returns:
        {
            "title": str,
            "sections": [{"section": str, "content": str}],
            "clean_text": str
        }
        """
        if not html or not html.strip():
            return None

        db = SessionLocal()

        try:
            # If crawl_session_id not passed explicitly, resolve from crawl_id
            resolved_crawl_session_id = crawl_session_id
            if resolved_crawl_session_id is None and crawl_id:
                session_row = db.query(CrawlSession).filter(
                    CrawlSession.crawl_id == crawl_id
                ).first()
                if session_row:
                    resolved_crawl_session_id = session_row.id

            soup = BeautifulSoup(html, "lxml")

            # Remove noisy tags
            for tag in soup([
                "script", "style", "nav", "footer", "header",
                "aside", "noscript", "form", "iframe", "svg"
            ]):
                tag.decompose()

            # Remove common noisy blocks by class
            for element in soup.find_all(
                attrs={
                    "class": re.compile(
                        r"ad|ads|banner|promo|sidebar|breadcrumb|popup|share|social|newsletter|comment|related",
                        re.I
                    )
                }
            ):
                element.decompose()

            # Remove common noisy blocks by id
            for element in soup.find_all(
                attrs={
                    "id": re.compile(
                        r"ad|ads|banner|promo|sidebar|breadcrumb|popup|share|social|newsletter|comment|related",
                        re.I
                    )
                }
            ):
                element.decompose()

            cleaned_html = str(soup)

            clean_text = trafilatura.extract(
                cleaned_html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                favor_precision=True
            )

            if not clean_text or len(clean_text.strip()) < 100:
                return None

            title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else "No Title"
            )

            sections = []
            current_heading = "Introduction"
            current_paragraphs = []

            for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                text = tag.get_text(" ", strip=True)

                if not text:
                    continue

                if tag.name in ["h1", "h2", "h3"]:
                    if current_paragraphs:
                        combined = "\n".join(current_paragraphs).strip()
                        if len(combined) > 80:
                            sections.append({
                                "section": current_heading,
                                "content": f"{current_heading}\n\n{combined}"
                            })

                    current_heading = text
                    current_paragraphs = []

                elif tag.name == "p":
                    if len(text) > 40:
                        current_paragraphs.append(text)

                elif tag.name == "li":
                    if len(text) > 20:
                        current_paragraphs.append(f"- {text}")

            if current_paragraphs:
                combined = "\n".join(current_paragraphs).strip()
                if len(combined) > 80:
                    sections.append({
                        "section": current_heading,
                        "content": f"{current_heading}\n\n{combined}"
                    })

            if not sections:
                paragraphs = [
                    p.get_text(" ", strip=True)
                    for p in soup.find_all("p")
                    if len(p.get_text(" ", strip=True)) > 40
                ]

                fallback_text = "\n".join(paragraphs).strip()

                if not fallback_text:
                    fallback_text = clean_text

                sections = [{
                    "section": "General",
                    "content": f"General\n\n{fallback_text}"
                }]

            now = datetime.utcnow()
            last_modified = headers.get("Last-Modified")
            content_hash = hashlib.md5(clean_text.encode("utf-8")).hexdigest()
            headings_text = "\n".join(sec["section"] for sec in sections)

            existing = db.query(PageMetadata).filter(PageMetadata.url == url).first()

            if existing:
                existing.title = title
                existing.headings = headings_text
                existing.last_modified = last_modified
                existing.content_hash = content_hash
                existing.crawled_at = now
                existing.last_checked = now
                existing.last_updated = now
                existing.crawl_id = crawl_id
                existing.crawl_session_id = resolved_crawl_session_id
            else:
                page = PageMetadata(
                    url=url,
                    title=title,
                    headings=headings_text,
                    last_modified=last_modified,
                    content_hash=content_hash,
                    crawled_at=now,
                    last_checked=now,
                    last_updated=now,
                    crawl_id=crawl_id,
                    crawl_session_id=resolved_crawl_session_id
                )
                db.add(page)

            db.commit()

            return {
                "title": title,
                "sections": sections,
                "clean_text": clean_text
            }

        except Exception as e:
            db.rollback()
            logger.exception(f"Extractor failed for {url}: {e}")
            return None
        finally:
            db.close()