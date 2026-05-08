"""Canonical immigration concept mapping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CanonicalConceptMapper:
    """Maps text snippets to canonical immigration concepts."""

    concept_variants: dict[str, tuple[str, ...]]

    def match_concepts(self, text: str) -> list[str]:
        lowered = text.lower()
        matched = [
            concept
            for concept, variants in self.concept_variants.items()
            if any(variant in lowered for variant in variants)
        ]
        return sorted(set(matched))


CANONICAL_CONCEPT_VARIANTS: dict[str, tuple[str, ...]] = {
    "bank_statements": (
        "proof of financial support",
        "proof of funds",
        "bank account statement",
        "bank statement",
        "financial evidence",
        "financial support",
    ),
    "passport": ("passport", "travel document"),
    "proof_of_relationship": (
        "family relationship proof",
        "proof of relationship",
        "relationship evidence",
    ),
    "employment_proof": ("employment proof", "proof of employment", "employment letter", "job letter"),
    "marriage_certificate": ("marriage certificate",),
    "police_certificates": ("police certificate", "criminal clearance certificate"),
    "medical_documents": ("medical document", "medical report", "medical examination report"),
    "invitation_letter": ("invitation letter", "letter of invitation"),
    "good_health": ("good health",),
    "no_criminal_convictions": ("no criminal", "criminal conviction", "criminal record", "inadmissible"),
    "proof_of_ties": ("proof of ties", "ties to home country", "home country ties"),
    "leave_canada_after_visit": ("leave canada", "leave by the end", "return to your country"),
    "proof_of_funds": ("sufficient funds", "proof of funds", "enough money"),
    "possible_medical_exam": ("possible medical exam", "medical exam", "medical examination"),
    "imm_5257": ("imm 5257", "imm5257"),
    "imm_5645": ("imm 5645", "imm5645"),
    "imm_5409": ("imm 5409", "imm5409"),
    "imm_5476": ("imm 5476", "imm5476"),
    "imm_5475": ("imm 5475", "imm5475"),
    "fees": ("fee", "fees", "$can"),
    "biometrics": ("biometric", "fingerprint"),
}
