"""Validation and QA layer for extracted IRCC dataset."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.validation.coverage_report import CoverageReport, ValidationReport
from app.validation.expected_data import EXPECTED_DATA
from app.validation.normalization import DEFAULT_CONCEPT_MAP, ConceptNormalizer
from app.validation.quality_metrics import MetricBreakdown, bounded_percentage, weighted_quality_score


@dataclass(slots=True)
class ValidationOutputs:
    validation_report_path: Path
    quality_metrics_path: Path
    missing_requirements_path: Path


class DatasetValidator:
    """Validates aggregated extraction against expected visitor visa concepts."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.aggregated_path = data_dir / "aggregated.json"
        self.normalizer = ConceptNormalizer(concept_map=DEFAULT_CONCEPT_MAP)

    def _load_pages(self) -> list[dict]:
        payload = json.loads(self.aggregated_path.read_text(encoding="utf-8"))
        return payload.get("pages", [])

    def _collect_concepts(self, pages: list[dict]) -> dict[str, list[str]]:
        eligibility_raw: list[str] = []
        supporting_raw: list[str] = []
        forms_raw: list[str] = []

        for page in pages:
            eligibility_raw.extend(page.get("eligibility_signals", []))
            supporting_raw.extend(page.get("supporting_document_signals", []))
            sections = page.get("sections", [])
            for section in sections:
                section_text = " ".join(
                    section.get("items", []) + section.get("bullets", []) + [section.get("heading", "")]
                )
                forms_raw.append(section_text)
                if section.get("category") == "eligibility_criteria":
                    eligibility_raw.append(section_text)
                if section.get("category") == "supporting_documents":
                    supporting_raw.append(section_text)
                if section.get("category") == "required_forms":
                    forms_raw.append(section_text)

        return {
            "eligibility_criteria": self.normalizer.normalize_concepts(eligibility_raw),
            "supporting_documents": self.normalizer.normalize_concepts(supporting_raw),
            "required_forms": self.normalizer.normalize_concepts(forms_raw),
        }

    def _coverage(self, extracted: list[str], expected: tuple[str, ...]) -> CoverageReport:
        extracted_set = set(extracted)
        expected_set = set(expected)
        missing = sorted(expected_set - extracted_set)
        duplicate_candidates = sorted([item for item in extracted if extracted.count(item) > 1])
        coverage = (len(extracted_set & expected_set) / len(expected_set) * 100.0) if expected_set else 0.0
        return CoverageReport(
            extracted_count=len(extracted_set),
            expected_count=len(expected_set),
            coverage_percent=bounded_percentage(coverage),
            missing_concepts=missing,
            duplicate_concepts=sorted(set(duplicate_candidates)),
        )

    def _section_completeness(self, pages: list[dict]) -> float:
        total_sections = 0
        complete_sections = 0
        for page in pages:
            for section in page.get("sections", []):
                total_sections += 1
                has_content = bool(section.get("items") or section.get("bullets") or section.get("tables"))
                if has_content:
                    complete_sections += 1
        if total_sections == 0:
            return 0.0
        return bounded_percentage((complete_sections / total_sections) * 100.0)

    def _category_accuracy(self, pages: list[dict], extracted: dict[str, list[str]]) -> float:
        """Heuristic category precision: expected concept presence inside matching sections."""
        expected_by_category = {
            "eligibility_criteria": set(EXPECTED_DATA.eligibility_criteria),
            "supporting_documents": set(EXPECTED_DATA.supporting_documents),
            "required_forms": set(EXPECTED_DATA.required_forms),
        }
        score_total = 0
        score_hits = 0

        for category, expected in expected_by_category.items():
            concepts = set(extracted.get(category, []))
            score_total += len(expected)
            score_hits += len(concepts & expected)

        if score_total == 0:
            return 0.0
        return bounded_percentage((score_hits / score_total) * 100.0)

    def generate_reports(self) -> ValidationOutputs:
        pages = self._load_pages()
        extracted = self._collect_concepts(pages)

        eligibility = self._coverage(extracted["eligibility_criteria"], EXPECTED_DATA.eligibility_criteria)
        supporting = self._coverage(extracted["supporting_documents"], EXPECTED_DATA.supporting_documents)
        forms = self._coverage(extracted["required_forms"], EXPECTED_DATA.required_forms)

        section_completeness = self._section_completeness(pages)
        category_accuracy = self._category_accuracy(pages, extracted)
        extraction_coverage = bounded_percentage(
            (eligibility.coverage_percent + supporting.coverage_percent + forms.coverage_percent) / 3.0
        )

        duplicate_union = (
            len(eligibility.duplicate_concepts)
            + len(supporting.duplicate_concepts)
            + len(forms.duplicate_concepts)
        )
        extracted_union = (
            max(1, eligibility.extracted_count) + max(1, supporting.extracted_count) + max(1, forms.extracted_count)
        )
        duplicate_percent = bounded_percentage((duplicate_union / extracted_union) * 100.0)

        validation_report = ValidationReport(
            eligibility=eligibility,
            supporting_documents=supporting,
            required_forms=forms,
            section_completeness_percent=section_completeness,
            category_accuracy_percent=category_accuracy,
        )

        metrics = MetricBreakdown(
            extraction_coverage_percent=extraction_coverage,
            category_accuracy_percent=category_accuracy,
            section_completeness_percent=section_completeness,
            duplicate_concept_percent=duplicate_percent,
            overall_quality_score=weighted_quality_score(
                extraction_coverage,
                category_accuracy,
                section_completeness,
                duplicate_percent,
            ),
        )

        missing_requirements = {
            "eligibility_criteria": eligibility.missing_concepts,
            "supporting_documents": supporting.missing_concepts,
            "required_forms": forms.missing_concepts,
        }

        validation_path = self.data_dir / "validation_report.json"
        quality_path = self.data_dir / "quality_metrics.json"
        missing_path = self.data_dir / "missing_requirements.json"

        validation_path.write_text(json.dumps(validation_report.to_dict(), indent=2), encoding="utf-8")
        quality_path.write_text(json.dumps(metrics.to_dict(), indent=2), encoding="utf-8")
        missing_path.write_text(json.dumps(missing_requirements, indent=2), encoding="utf-8")

        return ValidationOutputs(
            validation_report_path=validation_path,
            quality_metrics_path=quality_path,
            missing_requirements_path=missing_path,
        )
