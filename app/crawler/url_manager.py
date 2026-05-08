"""URL filtering and normalization logic."""

from __future__ import annotations

from urllib.parse import urlparse

from app.utils.helpers import is_same_or_subdomain, normalize_url


class URLManager:
    """Manages URL validation, normalization, and deduplication."""

    def __init__(self, allowed_domains: set[str], allowed_path_prefixes: tuple[str, ...] = ()) -> None:
        self.allowed_domains = {d.lower() for d in allowed_domains}
        self.allowed_path_prefixes = tuple(prefix.strip() for prefix in allowed_path_prefixes if prefix.strip())
        self.visited: set[str] = set()

    def sanitize_candidate(self, base_url: str, href: str) -> str | None:
        """Resolve and validate a candidate URL."""
        href_lower = href.lower().strip()
        if not href or href_lower.startswith(("mailto:", "javascript:", "#")):
            return None
        normalized = normalize_url(base_url, href)
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"}:
            return None
        if not is_same_or_subdomain(parsed.netloc, self.allowed_domains):
            return None
        if self.allowed_path_prefixes and not any(
            parsed.path.startswith(prefix) for prefix in self.allowed_path_prefixes
        ):
            return None
        return normalized

    def mark_visited(self, url: str) -> None:
        self.visited.add(url)

    def is_visited(self, url: str) -> bool:
        return url in self.visited
