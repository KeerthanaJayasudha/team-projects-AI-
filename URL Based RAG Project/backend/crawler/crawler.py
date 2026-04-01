import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque

from backend.crawler.robots_handler import RobotsHandler
from backend.crawler.url_utils import normalize_url, is_junk_url
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WebCrawler:
    def __init__(self, seed_urls: list, max_pages=50, max_depth=3):
        self.seed_urls = seed_urls
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.user_agent = "Mozilla/5.0 (compatible; URLRAGBot/1.0)"

    def crawl(self):
        visited = set()
        queued = set()
        queue = deque()
        pages_data = []

        # Normalize seed URLs first
        normalized_seeds = []
        for url in self.seed_urls:
            normalized = normalize_url(url)
            if normalized and normalized not in queued:
                normalized_seeds.append(normalized)
                queue.append((normalized, 0))
                queued.add(normalized)

        # Build allowed domains from normalized seeds
        allowed_domains = {
            urlparse(url).netloc.lower()
            for url in normalized_seeds
            if url
        }

        robots_handlers = {
            domain: RobotsHandler(f"https://{domain}")
            for domain in allowed_domains
        }

        while queue and len(visited) < self.max_pages:
            current_url, depth = queue.popleft()

            if not current_url:
                continue

            normalized_current = normalize_url(current_url)

            if not normalized_current:
                continue

            if normalized_current in visited:
                continue

            if depth > self.max_depth:
                continue

            parsed = urlparse(normalized_current)
            domain = parsed.netloc.lower()

            if domain not in allowed_domains:
                continue

            robots_handler = robots_handlers.get(domain)
            if robots_handler and not robots_handler.can_fetch(normalized_current):
                logger.info(f"Blocked by robots.txt: {normalized_current}")
                continue

            try:
                response = requests.get(
                    normalized_current,
                    headers={"User-Agent": self.user_agent},
                    timeout=10,
                    allow_redirects=True
                )
            except Exception as e:
                logger.warning(f"Request failed for {normalized_current}: {e}")
                continue

            if response.status_code != 200:
                logger.info(f"Skipping non-200 page: {normalized_current} | status={response.status_code}")
                continue

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                logger.info(f"Skipping non-HTML page: {normalized_current} | content-type={content_type}")
                continue

            # Use final redirected URL if any
            final_url = normalize_url(response.url)
            if not final_url:
                continue

            final_domain = urlparse(final_url).netloc.lower()
            if final_domain not in allowed_domains:
                logger.info(f"Redirect escaped allowed domains: {final_url}")
                continue

            if final_url in visited:
                continue

            visited.add(final_url)

            pages_data.append({
                "url": final_url,
                "html": response.text,
                "headers": dict(response.headers)
            })

            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all("a", href=True):
                raw_href = (link.get("href") or "").strip()

                if is_junk_url(raw_href):
                    continue

                next_url = urljoin(final_url, raw_href)
                normalized_next = normalize_url(next_url)

                if not normalized_next:
                    continue

                parsed_next = urlparse(normalized_next)
                next_domain = parsed_next.netloc.lower()

                if next_domain not in allowed_domains:
                    continue

                if normalized_next in visited:
                    continue

                if normalized_next in queued:
                    continue

                if depth + 1 <= self.max_depth:
                    queue.append((normalized_next, depth + 1))
                    queued.add(normalized_next)

        logger.info(f"Crawled {len(visited)} unique pages safely.")
        return pages_data