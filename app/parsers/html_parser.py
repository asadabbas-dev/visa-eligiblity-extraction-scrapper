"""HTML parsing utilities."""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from app.utils.constants import NOISE_SELECTORS


class HTMLParser:
    """Parses and sanitizes HTML into analyzable main content."""

    @staticmethod
    def parse(html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, "lxml")
        for selector in NOISE_SELECTORS:
            for node in soup.select(selector):
                node.decompose()
        return soup

    @staticmethod
    def extract_main(soup: BeautifulSoup) -> Tag:
        """Return main content container to avoid nav/footer noise."""
        for selector in ("main", "[role='main']", "#wb-cont", ".gc-main-content"):
            node = soup.select_one(selector)
            if isinstance(node, Tag):
                return node
        body = soup.body
        if not isinstance(body, Tag):
            raise ValueError("No parsable body/main content found")
        return body
