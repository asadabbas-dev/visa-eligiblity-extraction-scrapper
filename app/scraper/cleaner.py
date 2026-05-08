"""Content cleaning and deduplication utilities."""

from __future__ import annotations

from collections import OrderedDict

from app.utils.helpers import clean_text_block


class ContentCleaner:
    """Cleans extracted strings and list content."""

    @staticmethod
    def clean_items(items: list[str]) -> list[str]:
        cleaned = [clean_text_block(item) for item in items if clean_text_block(item)]
        return list(OrderedDict.fromkeys(cleaned))

    @staticmethod
    def clean_text(text: str) -> str:
        return clean_text_block(text)
