"""Entity extraction over structured IRCC pages."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.intelligence.concept_mapper import CANONICAL_CONCEPT_VARIANTS, CanonicalConceptMapper
from app.intelligence.confidence_scorer import ConfidenceScorer
from app.intelligence.semantic_matcher import SemanticMatcher


@dataclass(slots=True)
class ExtractedEntity:
    concept: str
    confidence: float
    source_heading: str
    source_url: str
    source_type: str
    category: str
    evidence: str

    def to_dict(self) -> dict:
        return asdict(self)


class EntityExtractor:
    """Extracts structured immigration entities with confidence metadata."""

    def __init__(self) -> None:
        self.mapper = CanonicalConceptMapper(CANONICAL_CONCEPT_VARIANTS)
        self.matcher = SemanticMatcher()
        self.scorer = ConfidenceScorer()

    def _extract_from_text(
        self,
        text: str,
        heading: str,
        url: str,
        source_type: str,
        category: str,
    ) -> list[ExtractedEntity]:
        direct_hits = self.mapper.match_concepts(text)
        fuzzy_hits = self.matcher.fuzzy_concept_hits(text, CANONICAL_CONCEPT_VARIANTS)
        fuzzy_map = {concept: score for concept, score in fuzzy_hits}

        entities: list[ExtractedEntity] = []
        for concept in set(direct_hits) | set(fuzzy_map):
            confidence = self.scorer.score(
                concept=concept,
                heading=heading,
                source_text=text,
                source_type=source_type,
                semantic_similarity=fuzzy_map.get(concept, 0.0),
            )
            entities.append(
                ExtractedEntity(
                    concept=concept,
                    confidence=confidence,
                    source_heading=heading,
                    source_url=url,
                    source_type=source_type,
                    category=category,
                    evidence=text[:400],
                )
            )
        return entities

    def extract(self, pages: list[dict]) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []
        for page in pages:
            url = page.get("url", "")
            for section in page.get("sections", []):
                heading = section.get("heading", "")
                category = section.get("category", "")
                for item in section.get("items", []):
                    entities.extend(self._extract_from_text(item, heading, url, "paragraph", category))
                for bullet in section.get("bullets", []):
                    entities.extend(self._extract_from_text(bullet, heading, url, "bullet", category))
                for table in section.get("tables", []):
                    for row in table:
                        row_text = " ".join(f"{k}: {v}" for k, v in row.items())
                        entities.extend(self._extract_from_text(row_text, heading, url, "table", category))
        dedup: dict[tuple[str, str, str, str], ExtractedEntity] = {}
        for entity in entities:
            key = (entity.concept, entity.source_url, entity.source_heading, entity.source_type)
            current = dedup.get(key)
            if current is None or entity.confidence > current.confidence:
                dedup[key] = entity
        return list(dedup.values())
