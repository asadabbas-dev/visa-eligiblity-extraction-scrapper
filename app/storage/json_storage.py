"""JSON storage for page-level and aggregate outputs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.scraper.extractor import PageData
from app.storage.file_manager import FileManager
from app.utils.helpers import slugify_url


@dataclass(slots=True)
class CrawlMetadata:
    seed_urls: list[str]
    total_discovered_urls: int
    total_scraped_pages: int
    skipped_by_robots: int
    failed_requests: int
    generated_at: str


class JSONStorage:
    """Persists crawler and scraper outputs as clean JSON files."""

    def __init__(self, output_dir: Path) -> None:
        self.manager = FileManager(output_dir)

    def save_page(self, page: PageData) -> Path:
        path = self.manager.page_path(slugify_url(page.url))
        path.write_text(json.dumps(page.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def save_aggregate(self, pages: list[PageData]) -> Path:
        payload = {"pages": [page.to_dict() for page in pages], "count": len(pages)}
        path = self.manager.aggregate_path()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def save_metadata(self, metadata: CrawlMetadata) -> Path:
        path = self.manager.metadata_path()
        path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
        return path

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
