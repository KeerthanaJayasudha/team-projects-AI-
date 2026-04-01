from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "fbclid",
    "gclid",
}


def is_junk_url(url: str) -> bool:
    """
    Reject links that should never be crawled.
    """
    if not url:
        return True

    raw = url.strip().lower()

    if not raw:
        return True

    if raw.startswith("#"):
        return True

    if raw.startswith("javascript:"):
        return True

    if raw.startswith("mailto:"):
        return True

    if raw.startswith("tel:"):
        return True

    if raw.startswith("data:"):
        return True

    return False


def normalize_url(url: str) -> str:
    """
    Normalize URLs to avoid duplicate crawling.
    - Default scheme to https if missing
    - Lowercase scheme + domain
    - Remove fragments
    - Remove tracking parameters
    - Sort query parameters
    - Remove trailing slash (except root)
    - Remove default ports
    - Collapse repeated slashes in path
    """

    if not url or is_junk_url(url):
        return ""

    parsed = urlparse(url.strip())

    # Handle missing scheme like: www.example.com/page
    if not parsed.scheme and not parsed.netloc:
        parsed = urlparse(f"https://{url.strip()}")

    scheme = parsed.scheme.lower() if parsed.scheme else "https"
    netloc = parsed.netloc.lower()

    # Remove default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"

    # Collapse repeated slashes
    path = re.sub(r"/+", "/", path)

    # Remove fragment
    fragment = ""

    query_dict = parse_qs(parsed.query)

    cleaned_query = {
        k: v for k, v in query_dict.items()
        if k.lower() not in TRACKING_PARAMS
    }

    sorted_query = urlencode(sorted(cleaned_query.items()), doseq=True)

    # Remove trailing slash except root
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    normalized = urlunparse((
        scheme,
        netloc,
        path,
        "",
        sorted_query,
        fragment
    ))

    return normalized