"""Project-wide constants and defaults."""

from __future__ import annotations

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "eligibility_criteria": (
        "eligibility",
        "who can",
        "requirements",
        "qualify",
        "valid passport",
        "good health",
        "criminal",
        "proof of ties",
        "leave canada",
        "enough money",
        "funds",
    ),
    "supporting_documents": (
        "supporting document",
        "document checklist",
        "evidence",
        "bank statement",
        "employment proof",
        "marriage certificate",
        "proof of relationship",
        "police certificate",
        "medical document",
    ),
    "required_forms": ("form", "imm", "application form"),
    "financial_requirements": ("fund", "financial", "bank statement", "money"),
    "proof_of_ties": ("ties to", "home country", "return to your country"),
    "biometrics": ("biometric", "fingerprint"),
    "inadmissibility": ("inadmissible", "criminal", "security risk"),
    "medical_requirements": ("medical exam", "medical examination", "good health"),
    "invitation_letters": ("invitation letter", "host letter"),
    "application_steps": ("how to apply", "apply", "step", "process"),
    "processing_information": ("processing time", "processing fee", "decision"),
    "travel_requirements": ("travel document", "passport", "entry requirement"),
}

CATEGORY_KEYWORD_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "eligibility_criteria": (
        ("eligibility", "who can", "who can apply"),
        ("requirement", "requirements", "must"),
        ("good health", "healthy"),
        ("criminal", "inadmissible", "conviction"),
        ("passport", "travel document"),
        ("leave canada", "return", "home country"),
    ),
    "supporting_documents": (
        ("supporting document", "document checklist"),
        ("proof", "evidence"),
        ("bank statement", "financial statement"),
        ("employment letter", "proof of employment"),
        ("marriage certificate", "proof of relationship"),
        ("police certificate", "medical document"),
    ),
    "required_forms": (
        ("imm", "form"),
        ("application form", "guide"),
        ("pdf", "download form"),
    ),
    "financial_requirements": (
        ("fund", "funds", "money"),
        ("financial support", "bank statement"),
    ),
    "proof_of_ties": (
        ("ties", "home country"),
        ("return", "leave canada"),
    ),
    "biometrics": (("biometric", "fingerprint"),),
    "inadmissibility": (("inadmissible", "criminal"),),
    "medical_requirements": (("medical exam", "medical examination", "health"),),
    "invitation_letters": (("invitation letter", "letter of invitation"),),
    "application_steps": (
        ("how to apply", "apply"),
        ("step", "steps", "process"),
    ),
    "processing_information": (("processing time", "fee", "decision"),),
    "travel_requirements": (("travel document", "entry requirement", "passport"),),
}

CANONICAL_ELIGIBILITY_SIGNALS: dict[str, tuple[str, ...]] = {
    "valid passport/travel document": ("valid passport", "travel document"),
    "good health": ("good health",),
    "no criminal convictions": ("no criminal", "criminal conviction", "inadmissible"),
    "proof of ties to home country": ("ties to your home", "proof of ties", "home country"),
    "proof applicant will leave Canada": ("leave canada", "leave by the end"),
    "sufficient funds": ("enough money", "sufficient funds", "financial support"),
    "possible medical exam": ("medical exam", "medical examination"),
    "invitation letter": ("invitation letter",),
}

CANONICAL_SUPPORTING_DOCUMENTS: dict[str, tuple[str, ...]] = {
    "passport": ("passport", "travel document"),
    "bank statements": ("bank statement", "financial statement"),
    "invitation letter": ("invitation letter",),
    "employment proof": ("employment proof", "employment letter", "proof of employment", "job letter"),
    "marriage certificate": ("marriage certificate",),
    "proof of relationship": ("proof of relationship",),
    "police certificates": ("police certificate",),
    "medical documents": ("medical document", "medical report", "medical exam"),
}

NOISE_SELECTORS: tuple[str, ...] = (
    "header",
    "footer",
    "nav",
    ".gcweb-menu",
    ".followus",
    ".breadcrumbs",
    ".cmp-banner",
    ".cookie-banner",
    ".provisional",
    ".pager",
    ".gc-subway",
)

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; IRCCCrawler/1.0; "
        "+https://www.canada.ca/en/immigration-refugees-citizenship.html)"
    )
}
