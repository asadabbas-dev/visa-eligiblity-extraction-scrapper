"""Keyword-based section classifier with easy extensibility."""

from __future__ import annotations

from app.utils.constants import CATEGORY_KEYWORD_GROUPS, CATEGORY_KEYWORDS


class SectionClassifier:
    """Classifies semantic section headings/content into categories."""

    def __init__(
        self,
        keyword_map: dict[str, tuple[str, ...]] | None = None,
        keyword_groups: dict[str, tuple[tuple[str, ...], ...]] | None = None,
    ) -> None:
        self.keyword_map = keyword_map or CATEGORY_KEYWORDS
        self.keyword_groups = keyword_groups or CATEGORY_KEYWORD_GROUPS

    def classify(self, heading: str, section_text: str) -> str:
        text = f"{heading} {section_text}".lower()
        best_category = "processing_information"
        best_score = 0.0

        for category, keywords in self.keyword_map.items():
            keyword_hits = sum(1 for kw in keywords if kw in text)
            group_hits = 0
            for group in self.keyword_groups.get(category, ()):
                if any(token in text for token in group):
                    group_hits += 1
            heading_boost = 1.5 if any(kw in heading.lower() for kw in keywords) else 0.0
            score = float(keyword_hits) + (group_hits * 2.0) + heading_boost
            if score > best_score:
                best_category = category
                best_score = score
        return best_category
