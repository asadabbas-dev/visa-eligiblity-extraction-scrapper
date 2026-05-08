"""File management helpers for output paths."""

from __future__ import annotations

from pathlib import Path


class FileManager:
    """Manages output directories and file creation."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.pages_dir = base_dir / "pages"
        self.meta_dir = base_dir / "metadata"
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def page_path(self, slug: str) -> Path:
        return self.pages_dir / f"{slug}.json"

    def aggregate_path(self) -> Path:
        return self.base_dir / "aggregated.json"

    def metadata_path(self) -> Path:
        return self.meta_dir / "crawl_metadata.json"
