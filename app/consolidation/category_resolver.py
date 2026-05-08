"""Resolve canonical concept slugs and classifier categories to output buckets."""

from __future__ import annotations

from typing import Literal

OutputCategory = Literal[
    "eligibility_criteria",
    "supporting_documents",
    "required_forms",
    "financial_requirements",
    "medical_requirements",
    "biometrics_requirements",
    "invitation_requirements",
    "proof_of_ties_requirements",
]

# Entity classifier categories → primary output bucket hints.
SECTION_CATEGORY_HINT: dict[str, OutputCategory] = {
    "eligibility_criteria": "eligibility_criteria",
    "supporting_documents": "supporting_documents",
    "required_forms": "required_forms",
    "financial_requirements": "financial_requirements",
    "medical_requirements": "medical_requirements",
    "biometrics": "biometrics_requirements",
    "invitation_letters": "invitation_requirements",
    "proof_of_ties": "proof_of_ties_requirements",
    "travel_requirements": "supporting_documents",
    "application_steps": "supporting_documents",
    "processing_information": "eligibility_criteria",
    "inadmissibility": "eligibility_criteria",
}

# Canonical concept slug → output category (imm_* handled separately).
SLUG_TO_CATEGORY: dict[str, OutputCategory] = {
    "good_health": "eligibility_criteria",
    "no_criminal_convictions": "eligibility_criteria",
    "leave_canada_after_visit": "eligibility_criteria",
    "proof_of_ties": "proof_of_ties_requirements",
    "proof_of_funds": "financial_requirements",
    "possible_medical_exam": "medical_requirements",
    "medical_documents": "medical_requirements",
    "invitation_letter": "invitation_requirements",
    "passport": "supporting_documents",
    "bank_statements": "supporting_documents",
    "employment_proof": "supporting_documents",
    "proof_of_relationship": "supporting_documents",
    "marriage_certificate": "supporting_documents",
    "police_certificates": "supporting_documents",
    "biometrics": "biometrics_requirements",
    "fees": "financial_requirements",
}

def is_form_slug(slug: str) -> bool:
    s = slug.lower().replace("-", "_")
    if s.startswith("imm_") and s[4:8].isdigit():
        return True
    import re

    return bool(re.fullmatch(r"imm\d{4}", s))


def resolve_category(slug: str, entity_category: str | None) -> OutputCategory:
    """Pick output bucket for a normalized concept slug."""
    if is_form_slug(slug):
        return "required_forms"
    if slug in SLUG_TO_CATEGORY:
        return SLUG_TO_CATEGORY[slug]
    if entity_category and entity_category in SECTION_CATEGORY_HINT:
        return SECTION_CATEGORY_HINT[entity_category]
    return "supporting_documents"


def eligibility_signal_to_labels() -> dict[str, tuple[OutputCategory, str]]:
    """Map aggregated eligibility_signals string keys to category + display fragment."""
    return {
        "good health": ("eligibility_criteria", "Good health"),
        "valid passport/travel document": ("eligibility_criteria", "Valid passport or travel document"),
        "no criminal convictions": ("eligibility_criteria", "No criminal or immigration-related convictions"),
        "proof of ties to home country": ("proof_of_ties_requirements", "Proof of ties to home country"),
        "proof applicant will leave canada": ("eligibility_criteria", "Proof applicant will leave Canada after visit"),
        "sufficient funds": ("financial_requirements", "Sufficient funds for your stay"),
        "possible medical exam": ("medical_requirements", "Medical exam (if required)"),
        "invitation letter": ("invitation_requirements", "Invitation letter (if applicable)"),
    }


def supporting_signal_to_labels() -> dict[str, tuple[OutputCategory, str]]:
    return {
        "passport": ("supporting_documents", "Passport / travel document"),
        "bank statements": ("supporting_documents", "Bank statements"),
        "employment proof": ("supporting_documents", "Employment proof"),
        "marriage certificate": ("supporting_documents", "Marriage certificate"),
        "proof of relationship": ("supporting_documents", "Proof of relationship"),
        "police certificates": ("supporting_documents", "Police certificates"),
        "medical documents": ("supporting_documents", "Medical documents"),
    }
