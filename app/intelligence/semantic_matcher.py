"""Deterministic fuzzy semantic matcher with synonym support."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(slots=True)
class SemanticMatcher:
    """Performs deterministic semantic matching over concept vocabularies."""

    min_similarity: float = 0.76

    def similarity(self, source: str, target: str) -> float:
        return SequenceMatcher(None, source.lower().strip(), target.lower().strip()).ratio()

    def best_match(self, text: str, candidates: tuple[str, ...]) -> tuple[str | None, float]:
        best_value: str | None = None
        best_score = 0.0
        for candidate in candidates:
            score = self.similarity(text, candidate)
            if score > best_score:
                best_value, best_score = candidate, score
        if best_score >= self.min_similarity:
            return best_value, best_score
        return None, best_score

    def fuzzy_concept_hits(self, text: str, variant_map: dict[str, tuple[str, ...]]) -> list[tuple[str, float]]:
        hits: list[tuple[str, float]] = []
        for concept, variants in variant_map.items():
            best_variant, score = self.best_match(text, variants)
            if best_variant:
                hits.append((concept, score))
        return sorted(hits, key=lambda item: item[1], reverse=True)
