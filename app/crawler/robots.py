"""robots.txt compliance helper."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from app.utils.constants import DEFAULT_HEADERS


class RobotsManager:
    """Caches robot parsers by host and validates path access."""

    def __init__(
        self,
        user_agent: str,
        timeout: int,
        logger: logging.Logger,
        fail_open: bool = True,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.logger = logger
        self.fail_open = fail_open
        self._parsers: dict[str, RobotFileParser] = {}

    def _get_parser(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        host_key = f"{parsed.scheme}://{parsed.netloc}"
        if host_key in self._parsers:
            return self._parsers[host_key]
        robots_url = f"{host_key}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            response = requests.get(
                robots_url,
                timeout=self.timeout,
                headers=DEFAULT_HEADERS,
            )
            response.raise_for_status()
            parser.parse(response.text.splitlines())
        except requests.RequestException as exc:
            self.logger.warning(
                "robots.txt fetch failed for %s (%s). Using fail_open=%s",
                robots_url,
                exc,
                self.fail_open,
            )
            if self.fail_open:
                parser.parse(["User-agent: *", "Allow: /"])
            else:
                parser.parse(["User-agent: *", "Disallow: /"])
        self._parsers[host_key] = parser
        return parser

    def can_fetch(self, url: str) -> bool:
        """Return True if robots allows crawling this URL."""
        parser = self._get_parser(url)
        return parser.can_fetch(self.user_agent, url)
