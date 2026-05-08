"""Extract scored requirement candidates from all pipeline outputs."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.consolidation.category_resolver import (
    eligibility_signal_to_labels,
    resolve_category,
    supporting_signal_to_labels,
)
from app.consolidation.deduplicator import normalize_entity_concept


NOISE_HEADINGS: frozenset[str] = frozenset(
    h.lower()
    for h in (
        "Page details",
        "On this page",
        "On this page:",
        "Features",
    )
)

MIN_CONFIDENCE = 0.4


@dataclass(slots=True)
class RequirementCandidate:
    """Single scored requirement line candidate."""

    category: str
    display_text: str
    score: float
    source: str  # entities | aggregated_signals | aggregated_sections | canonical
    slug: str = ""


@dataclass
class ExtractionContext:
    """Graph connectivity for orphan filtering."""

    connected_concepts: set[str] = field(default_factory=set)


def _heading_ok(heading: str) -> bool:
    h = heading.strip().lower()
    return bool(h) and h not in NOISE_HEADINGS


def extract_from_entities(entities: list[dict]) -> list[RequirementCandidate]:
    out: list[RequirementCandidate] = []
    for ent in entities:
        conf = float(ent.get("confidence", 0.0))
        if conf < MIN_CONFIDENCE:
            continue
        slug = normalize_entity_concept(str(ent.get("concept", "")))
        if not slug:
            continue
        heading = str(ent.get("source_heading", ""))
        if heading and not _heading_ok(heading):
            continue
        cat = resolve_category(slug, ent.get("category"))
        # Score boost for heading alignment keywords
        boost = 0.0
        hl = heading.lower()
        if cat == "financial_requirements" and any(
            x in hl for x in ("fund", "fee", "pay", "financial")
        ):
            boost = 0.08
        if cat == "biometrics_requirements" and "biometric" in hl:
            boost = 0.08
        if cat == "proof_of_ties_requirements" and "tie" in hl:
            boost = 0.08
        score = min(1.0, conf + boost)
        out.append(
            RequirementCandidate(
                category=cat,
                display_text="",  # filled by consolidator via formatter
                score=score,
                source="entities",
                slug=slug,
            )
        )
    return out


def extract_from_aggregated_signals(pages: list[dict]) -> list[RequirementCandidate]:
    elig_map = eligibility_signal_to_labels()
    sup_map = supporting_signal_to_labels()
    out: list[RequirementCandidate] = []
    for page in pages:
        for sig in page.get("eligibility_signals", []):
            key = str(sig).lower().strip()
            if key in elig_map:
                cat, label = elig_map[key]
                out.append(
                    RequirementCandidate(
                        category=cat,
                        display_text=label,
                        score=0.92,
                        source="aggregated_signals",
                        slug=key.replace(" ", "_"),
                    )
                )
        for sig in page.get("supporting_document_signals", []):
            key = str(sig).lower().strip()
            if key in sup_map:
                cat, label = sup_map[key]
                out.append(
                    RequirementCandidate(
                        category=cat,
                        display_text=label,
                        score=0.9,
                        source="aggregated_signals",
                        slug=key.replace(" ", "_"),
                    )
                )
    return out


def extract_from_sections(pages: list[dict]) -> list[RequirementCandidate]:
    """Use classifier categories on sections for high-recall hints."""
    out: list[RequirementCandidate] = []
    wanted_categories = {
        "eligibility_criteria",
        "supporting_documents",
        "required_forms",
        "financial_requirements",
        "medical_requirements",
        "biometrics",
        "invitation_letters",
        "proof_of_ties",
    }
    for page in pages:
        for sec in page.get("sections", []):
            heading = str(sec.get("heading", ""))
            if not _heading_ok(heading):
                continue
            cat_cls = str(sec.get("category", ""))
            if cat_cls not in wanted_categories:
                continue
            texts: list[str] = []
            texts.extend(sec.get("items", []))
            texts.extend(sec.get("bullets", []))
            for raw in texts:
                line = str(raw).strip()
                if len(line) < 15:
                    continue
                if any(x in line.lower() for x in ("cookie", "subscribe", "twitter")):
                    continue
                # Light scoring: longer evidence slightly stronger
                score = 0.55 + min(0.15, len(line) / 800.0)
                bucket = resolve_category("", cat_cls)
                out.append(
                    RequirementCandidate(
                        category=bucket,
                        display_text=_truncate_sentence(line),
                        score=score,
                        source="aggregated_sections",
                        slug="",
                    )
                )
    return out


def _truncate_sentence(text: str, max_len: int = 220) -> str:
    t = " ".join(text.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def extract_from_canonical(canonical: list[dict]) -> list[RequirementCandidate]:
    out: list[RequirementCandidate] = []
    for row in canonical:
        slug = normalize_entity_concept(str(row.get("concept", "")))
        if not slug:
            continue
        occ = int(row.get("occurrences", 1))
        score = min(0.88, 0.5 + 0.05 * min(occ, 8))
        cat = resolve_category(slug, None)
        out.append(
            RequirementCandidate(
                category=cat,
                display_text="",
                score=score,
                source="canonical",
                slug=slug,
            )
        )
    return out


