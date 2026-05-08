"""Coverage and confidence distribution checks."""

from __future__ import annotations

from collections import Counter, defaultdict


class ConceptCoverageChecker:
    """Computes found/missing/duplicate/weak concept metrics."""

    def analyze(self, entities: list[dict], missing_critical_concepts: list[str]) -> dict:
        concepts = [str(entity.get("concept", "")).lower() for entity in entities if entity.get("concept")]
        counter = Counter(concepts)
        duplicates = sorted([concept for concept, count in counter.items() if count > 1])

        weak_entities = [
            entity
            for entity in entities
            if isinstance(entity.get("confidence"), (float, int)) and float(entity["confidence"]) < 0.5
        ]
        weak_concepts = sorted({str(entity.get("concept", "")).lower() for entity in weak_entities if entity.get("concept")})

        confidence_buckets = {
            "lt_0_5": len([e for e in entities if float(e.get("confidence", 0.0)) < 0.5]),
            "0_5_to_0_7": len([e for e in entities if 0.5 <= float(e.get("confidence", 0.0)) < 0.7]),
            "0_7_to_0_85": len([e for e in entities if 0.7 <= float(e.get("confidence", 0.0)) < 0.85]),
            "gte_0_85": len([e for e in entities if float(e.get("confidence", 0.0)) >= 0.85]),
        }

        category_conf: dict[str, list[float]] = defaultdict(list)
        for entity in entities:
            category = str(entity.get("category", "unknown"))
            category_conf[category].append(float(entity.get("confidence", 0.0)))
        low_conf_categories = sorted(
            category
            for category, scores in category_conf.items()
            if scores and (sum(scores) / len(scores)) < 0.55
        )

        mean_conf = (sum(float(e.get("confidence", 0.0)) for e in entities) / len(entities)) if entities else 0.0
        confidence_quality_score = round(mean_conf * 100.0, 2)
        entity_trust_score = round(
            (
                (confidence_quality_score * 0.7)
                + ((1.0 - (len(weak_entities) / max(1, len(entities)))) * 30.0)
            ),
            2,
        )

        return {
            "found_concepts": sorted(counter.keys()),
            "missing_concepts": sorted(missing_critical_concepts),
            "duplicate_concepts": duplicates,
            "weak_confidence_concepts": weak_concepts,
            "confidence_distribution": confidence_buckets,
            "low_confidence_categories": low_conf_categories,
            "confidence_quality_score": confidence_quality_score,
            "entity_trust_score": entity_trust_score,
        }
