"""Quality metric models and scoring utilities."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class MetricBreakdown:
    extraction_coverage_percent: float
    category_accuracy_percent: float
    section_completeness_percent: float
    duplicate_concept_percent: float
    overall_quality_score: float

    def to_dict(self) -> dict:
        return asdict(self)


def bounded_percentage(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def weighted_quality_score(
    extraction_coverage: float,
    category_accuracy: float,
    section_completeness: float,
    duplicate_concept_percent: float,
) -> float:
    """Compute weighted quality score where fewer duplicates is better."""
    duplicate_health = 100.0 - duplicate_concept_percent
    score = (
        (0.4 * extraction_coverage)
        + (0.25 * category_accuracy)
        + (0.25 * section_completeness)
        + (0.1 * duplicate_health)
    )
    return bounded_percentage(score)
