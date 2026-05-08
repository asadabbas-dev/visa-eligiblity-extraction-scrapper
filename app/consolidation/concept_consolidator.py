"""Merge and rank requirement candidates per category."""

from __future__ import annotations

from collections import defaultdict

from app.consolidation.deduplicator import financial_canonical_slug
from app.consolidation.output_formatter import format_form_code, slug_to_display
from app.consolidation.requirement_extractor import RequirementCandidate

MIN_DISPLAY_SCORE = 0.42

OUTPUT_ORDER: tuple[str, ...] = (
    "eligibility_criteria",
    "supporting_documents",
    "required_forms",
    "financial_requirements",
    "medical_requirements",
    "biometrics_requirements",
    "invitation_requirements",
    "proof_of_ties_requirements",
)


def consolidate(candidates: list[RequirementCandidate]) -> dict[str, list[tuple[str, float]]]:
    """Return category -> sorted unique (display_text, score)."""
    scores_by_cat_label: dict[str, dict[str, tuple[str, float]]] = defaultdict(dict)

    for c in candidates:
        if c.display_text:
            label = c.display_text.strip()
            if not label:
                continue
            lk = label.lower()
            prev = scores_by_cat_label[c.category].get(lk, ("", 0.0))[1]
            if c.score >= prev:
                scores_by_cat_label[c.category][lk] = (label, c.score)
            continue

        slug = c.slug
        if not slug:
            continue
        cat = c.category
        if cat == "financial_requirements":
            slug = financial_canonical_slug(slug)
        label = format_form_code(slug) if cat == "required_forms" else slug_to_display(slug)
        if not label:
            continue
        lk = label.lower()
        _, prev_sc = scores_by_cat_label[cat].get(lk, ("", 0.0))
        scores_by_cat_label[cat][lk] = (label, max(prev_sc, c.score))

    out: dict[str, list[tuple[str, float]]] = {}
    for cat in OUTPUT_ORDER:
        rows: list[tuple[str, float]] = []
        for _lk, (lab, sc) in scores_by_cat_label.get(cat, {}).items():
            if sc < MIN_DISPLAY_SCORE:
                continue
            rows.append((lab, sc))
        rows.sort(key=lambda x: (-x[1], x[0].lower()))
        out[cat] = rows
    return out
