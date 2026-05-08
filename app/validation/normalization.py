"""Semantic normalization for extracted concepts."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.helpers import normalize_whitespace


@dataclass(slots=True)
class ConceptNormalizer:
    """Normalizes textual variants into canonical concept keys."""

    concept_map: dict[str, tuple[str, ...]]

    def normalize_text(self, text: str) -> str:
        cleaned = normalize_whitespace(text).lower()
        cleaned = re.sub(r"[^a-z0-9\s/_-]", " ", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    def normalize_concepts(self, values: list[str]) -> list[str]:
        normalized: set[str] = set()
        for raw in values:
            text = self.normalize_text(raw)
            for canonical, variants in self.concept_map.items():
                if any(variant in text for variant in variants):
                    normalized.add(canonical)
        return sorted(normalized)


DEFAULT_CONCEPT_MAP: dict[str, tuple[str, ...]] = {
    "proof_of_funds": ("enough money", "proof of funds", "financial support", "sufficient funds"),
    "valid_passport_or_travel_document": ("valid passport", "travel document", "passport"),
    "no_criminal_convictions": ("criminal record", "criminal convictions", "no criminal", "inadmissible"),
    "invitation_letter": ("invitation letter", "letter of invitation"),
    "proof_of_ties": ("proof of ties", "ties to home country", "home country ties"),
    "leave_canada_after_visit": ("leave canada", "leave by the end", "return to your country"),
    "possible_medical_exam": ("medical exam", "medical examination"),
    "good_health": ("good health",),
    "passport": ("passport", "travel document"),
    "bank_statements": ("bank statement", "financial statement"),
    "employment_proof": ("employment letter", "proof of employment", "job letter"),
    "marriage_certificate": ("marriage certificate",),
    "proof_of_relationship": ("proof of relationship",),
    "police_certificates": ("police certificate",),
    "medical_documents": ("medical document", "medical report"),
    "imm_5257": ("imm 5257", "imm5257"),
    "imm_5645": ("imm 5645", "imm5645"),
    "imm_5409": ("imm 5409", "imm5409"),
    "imm_5476": ("imm 5476", "imm5476"),
    "imm_5475": ("imm 5475", "imm5475"),
}
