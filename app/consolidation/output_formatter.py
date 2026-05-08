"""Human-readable labels for canonical requirement concepts."""

from __future__ import annotations

import re


_LABEL_OVERRIDES: dict[str, str] = {
    "good_health": "Good health",
    "no_criminal_convictions": "No criminal convictions",
    "proof_of_ties": "Proof of ties to home country",
    "leave_canada_after_visit": "Proof applicant will leave Canada after visit",
    "proof_of_funds": "Proof of funds / sufficient funds",
    "possible_medical_exam": "Medical exam (if required)",
    "invitation_letter": "Invitation letter (if applicable)",
    "passport": "Passport",
    "bank_statements": "Bank statements",
    "employment_proof": "Employment proof",
    "proof_of_relationship": "Proof of relationship",
    "police_certificates": "Police certificates",
    "medical_documents": "Medical documents",
    "marriage_certificate": "Marriage certificate",
    "biometrics": "Biometrics",
    "fees": "Applicable fees",
    "imm_5257": "IMM5257",
    "imm_5645": "IMM5645",
    "imm_5476": "IMM5476",
    "imm_5475": "IMM5475",
    "imm_5409": "IMM5409",
    "valid_passport_travel": "Valid passport or travel document",
}


def slug_to_display(slug: str) -> str:
    """Convert snake_case concept key to readable Title Case."""
    if not slug:
        return ""
    key = slug.lower().strip()
    if key in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[key]
    # imm_5257 or imm5257
    if key.startswith("imm_") and key[4:].isdigit():
        return f"IMM{key[4:]}"
    m = re.fullmatch(r"imm(\d{4})", key)
    if m:
        return f"IMM{m.group(1)}"
    words = key.replace("_", " ").split()
    return " ".join(w.capitalize() for w in words)


def format_form_code(slug: str) -> str:
    """Normalize IMM form identifiers to IMM5257 style."""
    key = slug.lower().replace("-", "_")
    if key.startswith("imm_") and key[4:].isdigit():
        return f"IMM{key[4:]}"
    m = re.fullmatch(r"imm(\d{4})", key)
    if m:
        return f"IMM{m.group(1)}"
    return slug_to_display(slug)
