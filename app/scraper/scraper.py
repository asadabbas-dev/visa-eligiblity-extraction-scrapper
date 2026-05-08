"""Page scraping orchestrator."""

from __future__ import annotations

import logging

import requests

from app.parsers.html_parser import HTMLParser
from app.parsers.pdf_parser import PDFParser
from app.scraper.extractor import PageData, SemanticExtractor
from app.utils.constants import DEFAULT_HEADERS
from app.utils.helpers import Settings


class IRCCScraper:
    """Scrapes one URL and returns structured extraction output."""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.extractor = SemanticExtractor()
        self.pdf_parser = PDFParser(logger=logger)
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _fetch_html(self, url: str) -> str:
        response = self.session.get(url, timeout=self.settings.request_timeout)
        response.raise_for_status()
        return response.text

    def scrape_page(self, url: str) -> PageData | None:
        try:
            html = self._fetch_html(url)
            soup = HTMLParser.parse(html)
            main = HTMLParser.extract_main(soup)
            extracted = self.extractor.extract(soup=soup, page_url=url, main_content=main)

            if self.settings.extract_pdf_text and extracted.pdf_links:
                pdf_dir = self.settings.data_dir / "pdfs"
                for pdf_url in extracted.pdf_links:
                    pdf_path = self.pdf_parser.download_pdf(
                        url=pdf_url,
                        output_dir=pdf_dir,
                        timeout=self.settings.request_timeout,
                    )
                    if not pdf_path:
                        continue
                    if self.settings.download_pdfs:
                        self.logger.info("PDF downloaded: %s", pdf_path)
                    if self.settings.extract_pdf_text:
                        pdf_text = self.pdf_parser.extract_text(pdf_path)
                        extracted.pdf_semantic_insights.append(
                            {
                                "pdf_url": pdf_url,
                                "semantic_requirements": self.pdf_parser.extract_semantic_requirements(pdf_text),
                            }
                        )
            return extracted
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.exception("Scrape failed for %s: %s", url, exc)
            return None
