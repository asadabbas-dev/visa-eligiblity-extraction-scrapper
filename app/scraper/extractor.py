"""Semantic heading-based extraction engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

from app.intelligence.hierarchy_parser import HierarchyParser
from app.scraper.cleaner import ContentCleaner
from app.scraper.classifier import SectionClassifier
from app.utils.constants import CANONICAL_ELIGIBILITY_SIGNALS, CANONICAL_SUPPORTING_DOCUMENTS


@dataclass(slots=True)
class SectionData:
    heading: str
    heading_level: str
    category: str
    items: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    tables: list[list[dict[str, str]]] = field(default_factory=list)


@dataclass(slots=True)
class PageData:
    page_title: str
    url: str
    h1: str
    headings: dict[str, list[str]]
    sections: list[SectionData]
    eligibility_signals: list[str]
    supporting_document_signals: list[str]
    hierarchy: list[dict]
    pdf_semantic_insights: list[dict]
    pdf_links: list[str]
    related_links: list[str]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["sections"] = [asdict(section) for section in self.sections]
        return payload


class SemanticExtractor:
    """Extracts sections by heading hierarchy and associates list/table content."""

    def __init__(self) -> None:
        self.cleaner = ContentCleaner()
        self.classifier = SectionClassifier()
        self.hierarchy_parser = HierarchyParser()

    def _extract_table(self, table: Tag) -> list[dict[str, str]]:
        rows = table.select("tr")
        if not rows:
            return []
        headers = [self.cleaner.clean_text(th.get_text(" ", strip=True)) for th in rows[0].select("th,td")]
        parsed_rows: list[dict[str, str]] = []
        for row in rows[1:]:
            cells = [self.cleaner.clean_text(td.get_text(" ", strip=True)) for td in row.select("td,th")]
            if not cells:
                continue
            if len(headers) == len(cells):
                parsed_rows.append(dict(zip(headers, cells)))
            else:
                parsed_rows.append({f"column_{i+1}": val for i, val in enumerate(cells)})
        return parsed_rows

    def _collect_section_nodes(self, heading: Tag) -> list[Tag]:
        nodes: list[Tag] = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, NavigableString):
                continue
            if not isinstance(sibling, Tag):
                continue
            if sibling.name in {"h1", "h2", "h3"}:
                break
            nodes.append(sibling)
        return nodes

    def _extract_signals(self, corpus: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
        text = corpus.lower()
        hits = [
            canonical
            for canonical, keywords in mapping.items()
            if any(keyword in text for keyword in keywords)
        ]
        return sorted(set(hits))

    def extract(self, soup: BeautifulSoup, page_url: str, main_content: Tag) -> PageData:
        page_title = self.cleaner.clean_text((soup.title.string if soup.title else "") or "")
        h1 = self.cleaner.clean_text(main_content.select_one("h1").get_text(" ", strip=True)) if main_content.select_one("h1") else ""
        h2s = [self.cleaner.clean_text(h.get_text(" ", strip=True)) for h in main_content.select("h2")]
        h3s = [self.cleaner.clean_text(h.get_text(" ", strip=True)) for h in main_content.select("h3")]

        pdf_links = [
            urljoin(page_url, a.get("href", ""))
            for a in main_content.select("a[href$='.pdf']")
            if a.get("href")
        ]
        related_links = [
            urljoin(page_url, a.get("href", ""))
            for a in main_content.select("a[href]")
            if a.get("href") and "javascript:" not in a.get("href", "").lower()
        ]

        sections: list[SectionData] = []
        headings = main_content.select("h2, h3")
        for heading in headings:
            heading_text = self.cleaner.clean_text(heading.get_text(" ", strip=True))
            nodes = self._collect_section_nodes(heading)
            items: list[str] = []
            bullets: list[str] = []
            tables: list[list[dict[str, str]]] = []

            for node in nodes:
                if node.name in {"p", "li"}:
                    items.append(node.get_text(" ", strip=True))
                elif node.name in {"ul", "ol"}:
                    bullets.extend(li.get_text(" ", strip=True) for li in node.select("li"))
                elif node.name == "table":
                    table_data = self._extract_table(node)
                    if table_data:
                        tables.append(table_data)

            cleaned_items = self.cleaner.clean_items(items)
            cleaned_bullets = self.cleaner.clean_items(bullets)
            section_text = " ".join(cleaned_items + cleaned_bullets)
            category = self.classifier.classify(heading_text, section_text)

            sections.append(
                SectionData(
                    heading=heading_text,
                    heading_level=heading.name,
                    category=category,
                    items=cleaned_items,
                    bullets=cleaned_bullets,
                    tables=tables,
                )
            )

        corpus = " ".join(
            [page_title, h1]
            + h2s
            + h3s
            + [item for sec in sections for item in (sec.items + sec.bullets)]
        )
        eligibility_signals = self._extract_signals(corpus, CANONICAL_ELIGIBILITY_SIGNALS)
        supporting_document_signals = self._extract_signals(corpus, CANONICAL_SUPPORTING_DOCUMENTS)

        return PageData(
            page_title=page_title,
            url=page_url,
            h1=h1,
            headings={"h2": h2s, "h3": h3s},
            sections=sections,
            eligibility_signals=eligibility_signals,
            supporting_document_signals=supporting_document_signals,
            hierarchy=[
                node.to_dict()
                for node in self.hierarchy_parser.build_tree([asdict(section) for section in sections])
            ],
            pdf_semantic_insights=[],
            pdf_links=sorted(set(pdf_links)),
            related_links=sorted(set(related_links)),
        )
