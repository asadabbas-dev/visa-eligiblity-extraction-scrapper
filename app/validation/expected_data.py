"""Gold-standard expected data for validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpectedExtractionData:
    """Expected canonical concepts for IRCC visitor visa extraction."""

    eligibility_criteria: tuple[str, ...] = (
        "valid_passport_or_travel_document",
        "good_health",
        "no_criminal_convictions",
        "proof_of_ties",
        "leave_canada_after_visit",
        "proof_of_funds",
        "possible_medical_exam",
        "invitation_letter",
    )
    supporting_documents: tuple[str, ...] = (
        "passport",
        "bank_statements",
        "invitation_letter",
        "employment_proof",
        "marriage_certificate",
        "proof_of_relationship",
        "police_certificates",
        "medical_documents",
    )
    required_forms: tuple[str, ...] = (
        "imm_5257",
        "imm_5645",
        "imm_5409",
        "imm_5476",
        "imm_5475",
    )


EXPECTED_DATA = ExpectedExtractionData()
