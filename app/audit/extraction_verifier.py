"""Verification of critical immigration concept extraction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CriticalConcepts:
    eligibility: tuple[str, ...] = (
        "passport",
        "good_health",
        "no_criminal_convictions",
        "proof_of_funds",
        "proof_of_ties",
        "leave_canada_after_visit",
        "medical_exam",
        "invitation_letter",
    )
    supporting_documents: tuple[str, ...] = (
        "bank_statements",
        "employment_proof",
        "marriage_certificate",
        "proof_of_relationship",
        "police_certificates",
        "medical_documents",
    )
    forms: tuple[str, ...] = ("imm5257", "imm5645", "imm5476")
    biometrics: tuple[str, ...] = ("biometrics",)


def normalize_concept(value: str) -> str:
    normalized = value.lower().replace("-", "_").replace(" ", "_")
    return normalized


class ExtractionVerifier:
    """Checks if required concepts appear in output datasets."""

    def __init__(self) -> None:
        self.critical = CriticalConcepts()

    def required_concepts(self) -> dict[str, set[str]]:
        return {
            "eligibility": {normalize_concept(v) for v in self.critical.eligibility},
            "supporting_documents": {normalize_concept(v) for v in self.critical.supporting_documents},
            "forms": {normalize_concept(v) for v in self.critical.forms},
            "biometrics": {normalize_concept(v) for v in self.critical.biometrics},
        }

    def verify(self, discovered_concepts: set[str]) -> dict:
        required = self.required_concepts()
        missing_by_group: dict[str, list[str]] = {}
        found_by_group: dict[str, list[str]] = {}

        for group, expected in required.items():
            hits = sorted(concept for concept in expected if concept in discovered_concepts)
            missing = sorted(expected - set(hits))
            found_by_group[group] = hits
            missing_by_group[group] = missing

        required_union = set().union(*required.values())
        coverage = (len(required_union & discovered_concepts) / len(required_union) * 100.0) if required_union else 0.0
        return {
            "required_concepts": {k: sorted(v) for k, v in required.items()},
            "found_by_group": found_by_group,
            "missing_by_group": missing_by_group,
            "coverage_percent": round(coverage, 2),
            "missing_critical_concepts": sorted(
                concept for missing_list in missing_by_group.values() for concept in missing_list
            ),
        }
