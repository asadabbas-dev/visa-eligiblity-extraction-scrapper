"""Helper utilities and runtime settings."""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse


@dataclass(slots=True)
class Settings:
    """Application configuration loaded from environment variables."""

    max_depth: int = int(os.getenv("MAX_DEPTH", "2"))
    max_pages: int = int(os.getenv("MAX_PAGES", "120"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
    request_retries: int = int(os.getenv("REQUEST_RETRIES", "3"))
    rate_limit_seconds: float = float(os.getenv("RATE_LIMIT_SECONDS", "0.8"))
    workers: int = int(os.getenv("WORKERS", "6"))
    obey_robots: bool = os.getenv("OBEY_ROBOTS", "true").lower() == "true"
    robots_fail_open: bool = os.getenv("ROBOTS_FAIL_OPEN", "true").lower() == "true"
    extract_pdf_text: bool = os.getenv("EXTRACT_PDF_TEXT", "false").lower() == "true"
    download_pdfs: bool = os.getenv("DOWNLOAD_PDFS", "false").lower() == "true"
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    logs_dir: Path = Path(os.getenv("LOGS_DIR", "logs"))
    crawl_path_allowlist: tuple[str, ...] = tuple(
        part.strip()
        for part in os.getenv(
            "CRAWL_PATH_ALLOWLIST",
            (
                "/en/immigration-refugees-citizenship/services/visit-canada,"
                "/en/immigration-refugees-citizenship/services/visit-canada/visitor-visa,"
                "/en/immigration-refugees-citizenship/services/visit-canada/eligibility,"
                "/en/immigration-refugees-citizenship/services/visit-canada/apply-visitor-visa,"
                "/en/immigration-refugees-citizenship/services/visit-canada/letter-invitation,"
                "/en/immigration-refugees-citizenship/services/application/common-supporting-documents,"
                "/en/immigration-refugees-citizenship/services/application/application-forms-guides/guide-5256-applying-visitor-visa-temporary-resident-visa,"
                "/en/immigration-refugees-citizenship/services/application/application-forms-guides/imm5257,"
                "/content/canadasite/en/immigration-refugees-citizenship/services/visit-canada"
            ),
        ).split(",")
        if part.strip()
    )


def normalize_whitespace(text: str) -> str:
    """Normalize unicode and collapse excessive whitespace."""
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def clean_text_block(text: str) -> str:
    """Sanitize malformed text block while keeping semantics."""
    text = normalize_whitespace(text)
    text = text.replace("\u00a0", " ")
    text = text.strip(" -\n\t")
    return text


def slugify_url(url: str) -> str:
    """Create a deterministic file-safe slug for a URL."""
    parsed = urlparse(url)
    host = parsed.netloc.replace(".", "_")
    path = parsed.path.strip("/") or "index"
    path = re.sub(r"[^a-zA-Z0-9/_-]", "", path).replace("/", "_")
    return f"{host}__{path}"


def is_same_or_subdomain(netloc: str, allowed_domains: set[str]) -> bool:
    """Check if host is within allowed root domains."""
    host = netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def normalize_url(base_url: str, href: str) -> str:
    """Resolve relative URL, drop fragments, and normalize scheme/host."""
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    cleaned = parsed._replace(fragment="", query=parsed.query.strip())
    normalized = urlunparse(cleaned)
    return normalized.rstrip("/")
