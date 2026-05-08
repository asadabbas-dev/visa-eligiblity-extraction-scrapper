"""Coverage and completeness reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class CoverageReport:
    extracted_count: int
    expected_count: int
    coverage_percent: float
    missing_concepts: list[str]
    duplicate_concepts: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ValidationReport:
    eligibility: CoverageReport
    supporting_documents: CoverageReport
    required_forms: CoverageReport
    section_completeness_percent: float
    category_accuracy_percent: float

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["eligibility"] = self.eligibility.to_dict()
        payload["supporting_documents"] = self.supporting_documents.to_dict()
        payload["required_forms"] = self.required_forms.to_dict()
        return payload
