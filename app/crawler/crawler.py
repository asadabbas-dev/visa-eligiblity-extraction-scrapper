"""Breadth-first crawler for IRCC pages."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.crawler.queue_manager import CrawlTask, QueueManager
from app.crawler.robots import RobotsManager
from app.crawler.url_manager import URLManager
from app.utils.constants import DEFAULT_HEADERS
from app.utils.helpers import Settings


@dataclass(slots=True)
class CrawlResult:
    """Crawled pages and discovery metadata."""

    discovered_urls: list[str]
    skipped_by_robots: int
    failed_requests: int


class BFSCrawler:
    """Recursive BFS crawler with depth control and deduplication."""

    def __init__(
        self,
        settings: Settings,
        logger: logging.Logger,
        allowed_domains: set[str],
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.url_manager = URLManager(
            allowed_domains=allowed_domains,
            allowed_path_prefixes=self.settings.crawl_path_allowlist,
        )
        self.queue = QueueManager()
        self.robots = RobotsManager(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            timeout=self.settings.request_timeout,
            logger=self.logger,
            fail_open=self.settings.robots_fail_open,
        )
        self.session = self._build_session()
        self._last_request_ts = 0.0

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=self.settings.request_retries,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods={"GET", "HEAD"},
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(DEFAULT_HEADERS)
        return session

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_ts
        wait_for = self.settings.rate_limit_seconds - elapsed
        if wait_for > 0:
            time.sleep(wait_for)

    def _fetch(self, url: str) -> str | None:
        self._rate_limit()
        self._last_request_ts = time.time()
        try:
            response = self.session.get(url, timeout=self.settings.request_timeout)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            return response.text
        except requests.RequestException as exc:
            self.logger.warning("Request failed for %s: %s", url, exc)
            return None

    def crawl(self, start_urls: list[str]) -> CrawlResult:
        """Crawl pages using BFS and return discovered URLs."""
        for url in start_urls:
            self.queue.enqueue(CrawlTask(url=url, depth=0))

        discovered: list[str] = []
        skipped_by_robots = 0
        failed_requests = 0

        while not self.queue.is_empty() and len(discovered) < self.settings.max_pages:
            task = self.queue.dequeue()
            if self.url_manager.is_visited(task.url):
                continue
            if task.depth > self.settings.max_depth:
                continue
            if self.settings.obey_robots and not self.robots.can_fetch(task.url):
                skipped_by_robots += 1
                self.logger.info("Skipping by robots.txt: %s", task.url)
                continue

            html = self._fetch(task.url)
            self.url_manager.mark_visited(task.url)
            if html is None:
                failed_requests += 1
                continue

            discovered.append(task.url)
            self.logger.info("Crawled depth=%s url=%s", task.depth, task.url)
            soup = BeautifulSoup(html, "lxml")
            for tag in soup.select("a[href]"):
                candidate = self.url_manager.sanitize_candidate(task.url, tag.get("href", ""))
                if not candidate or self.url_manager.is_visited(candidate):
                    continue
                self.queue.enqueue(CrawlTask(url=candidate, depth=task.depth + 1))

        return CrawlResult(
            discovered_urls=discovered,
            skipped_by_robots=skipped_by_robots,
            failed_requests=failed_requests,
        )
