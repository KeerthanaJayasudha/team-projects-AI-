from backend.crawler.crawler import crawl

def test_crawl_basic():
    urls = crawl("https://example.com", depth=1)
    assert isinstance(urls, list)
    assert len(urls) >= 1