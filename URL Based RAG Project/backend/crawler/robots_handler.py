import urllib.robotparser
from urllib.parse import urlparse

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RobotsHandler:
    def __init__(self, seed_url: str):
        parsed = urlparse(seed_url)
        self.base_domain = parsed.netloc
        self.scheme = parsed.scheme or "https"

        robots_url = f"{self.scheme}://{self.base_domain}/robots.txt"

        self.robot_parser = urllib.robotparser.RobotFileParser()
        self.robot_parser.set_url(robots_url)

        self.robots_loaded = False

        try:
            self.robot_parser.read()
            self.robots_loaded = True
        except Exception as e:
            logger.warning(f"Could not read robots.txt for {self.base_domain}: {e}")

    def can_fetch(self, url: str) -> bool:
        """
        If robots.txt is unavailable, allow crawling instead of blocking all pages.
        """
        try:
            if not self.robots_loaded:
                return True
            return self.robot_parser.can_fetch("*", url)
        except Exception:
            return True