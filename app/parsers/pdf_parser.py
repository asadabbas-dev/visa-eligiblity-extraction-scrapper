"""PDF parsing and optional downloading."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pdfplumber
import requests

from app.utils.helpers import clean_text_block, slugify_url


class PDFParser:
    """Handles PDF download and text extraction."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def download_pdf(self, url: str, output_dir: Path, timeout: int) -> Path | None:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{slugify_url(url)}.pdf"
        path = output_dir / filename
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            path.write_bytes(response.content)
            return path
        except requests.RequestException as exc:
            self.logger.warning("PDF download failed %s: %s", url, exc)
            return None

    def extract_text(self, pdf_path: Path) -> str:
        chunks: list[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                chunks.append(clean_text_block(page.extract_text() or ""))
        return "\n".join(chunk for chunk in chunks if chunk)

    def extract_semantic_requirements(self, text: str) -> dict[str, list[str]]:
        """Extract checklist/forms/docs/regional cues from PDF text."""
        lines = [clean_text_block(line) for line in text.splitlines() if clean_text_block(line)]
        blob = " ".join(lines).lower()

        checklist = [line for line in lines if re.search(r"\b(checklist|required|must include)\b", line.lower())]
        forms = sorted(set(re.findall(r"\bimm[\s-]?\d{4}\b", blob)))
        supporting_docs = [
            line
            for line in lines
            if re.search(
                r"\b(passport|bank statement|invitation letter|employment|marriage|relationship|police|medical)\b",
                line.lower(),
            )
        ]
        regional_requirements = [
            line
            for line in lines
            if re.search(r"\b(country|region|visa office|local requirement)\b", line.lower())
        ]
        return {
            "document_checklists": checklist[:80],
            "required_forms": forms,
            "supporting_documents": supporting_docs[:120],
            "regional_requirements": regional_requirements[:80],
        }
