"""Confidence scoring for extracted entities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConfidenceScorer:
    """Scores concept confidence using deterministic evidence signals."""

    def score(
        self,
        concept: str,
        heading: str,
        source_text: str,
        source_type: str,
        semantic_similarity: float = 0.0,
    ) -> float:
        heading_lower = heading.lower()
        text_lower = source_text.lower()
        score = 0.4

        if concept.replace("_", " ") in text_lower:
            score += 0.2
        if concept.split("_")[0] in heading_lower:
            score += 0.12
        if source_type in {"bullet", "table"}:
            score += 0.1
        if source_type == "pdf":
            score += 0.05
        score += min(0.18, semantic_similarity * 0.18)
        return round(min(0.99, score), 3)
