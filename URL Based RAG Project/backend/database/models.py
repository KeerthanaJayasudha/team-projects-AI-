from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class CrawlSource(Base):
    __tablename__ = "crawl_sources"

    id = Column(Integer, primary_key=True, index=True)
    seed_url = Column(String, unique=True, nullable=False, index=True)
    max_depth = Column(Integer, nullable=False, default=2)
    max_pages = Column(Integer, nullable=False, default=50)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_crawled = Column(DateTime, nullable=True)

    sessions = relationship("CrawlSession", back_populates="source", cascade="all, delete-orphan")


class CrawlSession(Base):
    __tablename__ = "crawl_sessions"

    id = Column(Integer, primary_key=True, index=True)
    crawl_id = Column(String, unique=True, nullable=False, index=True)

    source_id = Column(Integer, ForeignKey("crawl_sources.id"), nullable=True)
    update_strategy = Column(String, nullable=False, default="incremental")

    status = Column(String, nullable=False, default="started")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    pages_crawled = Column(Integer, default=0, nullable=False)
    pages_processed = Column(Integer, default=0, nullable=False)
    sections_seen = Column(Integer, default=0, nullable=False)
    sections_updated = Column(Integer, default=0, nullable=False)
    documents_indexed = Column(Integer, default=0, nullable=False)

    error_message = Column(Text, nullable=True)

    source = relationship("CrawlSource", back_populates="sessions")
    pages = relationship("PageMetadata", back_populates="crawl_session")


class PageMetadata(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    headings = Column(Text, nullable=True)
    last_modified = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)

    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=True)

    crawl_session_id = Column(Integer, ForeignKey("crawl_sessions.id"), nullable=True)
    crawl_id = Column(String, nullable=True, index=True)

    crawl_session = relationship("CrawlSession", back_populates="pages")


class PageHash(Base):
    __tablename__ = "page_hashes"

    # stored as "<url>::<section>"
    url = Column(String, primary_key=True)
    content_hash = Column(String, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    crawl_id = Column(String, nullable=True, index=True)