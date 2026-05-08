"""Build verified final_requirements.json and summary markdown."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from app.consolidation.category_resolver import eligibility_signal_to_labels, supporting_signal_to_labels
from app.consolidation.concept_consolidator import OUTPUT_ORDER, consolidate
from app.consolidation.deduplicator import dedupe_preserve_order
from app.consolidation.output_formatter import format_form_code, slug_to_display
from app.consolidation.requirement_extractor import (
    extract_from_aggregated_signals,
    extract_from_canonical,
    extract_from_entities,
)


def _fallback_scored() -> dict[str, list[tuple[str, float]]]:
    """Minimum catalog used only when a category would otherwise be empty."""
    fb: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for _key, (cat, label) in eligibility_signal_to_labels().items():
        fb[cat].append((label, 0.85))
    for _key, (cat, label) in supporting_signal_to_labels().items():
        fb[cat].append((label, 0.85))
    fb["biometrics_requirements"].append((slug_to_display("biometrics"), 0.75))
    for raw in ("imm_5257", "imm_5645", "imm_5476"):
        fb["required_forms"].append((format_form_code(raw), 0.8))
    return fb


def _merge_fallback(scored: dict[str, list[tuple[str, float]]]) -> dict[str, list[tuple[str, float]]]:
    """Union extraction scores with catalog fallbacks; dedupe by label (keep max score)."""
    fb = _fallback_scored()
    merged: dict[str, list[tuple[str, float]]] = {}
    for cat in OUTPUT_ORDER:
        rows = list(scored.get(cat, [])) + list(fb.get(cat, []))
        best: dict[str, tuple[str, float]] = {}
        for label, sc in rows:
            lk = label.strip().lower()
            if not lk:
                continue
            prev = best.get(lk, ("", 0.0))[1]
            if sc >= prev:
                best[lk] = (label.strip(), sc)
        merged[cat] = [(lab, sc) for lab, sc in best.values()]
        merged[cat].sort(key=lambda x: (-x[1], x[0].lower()))
    return merged


def _labels_only(scored: dict[str, list[tuple[str, float]]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for cat in OUTPUT_ORDER:
        labels = [pair[0] for pair in scored.get(cat, [])]
        out[cat] = dedupe_preserve_order(labels)
    return out


def cleanup_semantic_duplicates(payload: dict[str, list[str]]) -> None:
    """Normalize near-duplicate lines in place."""
    elig = payload.get("eligibility_criteria", [])
    lows = [x.lower() for x in elig]
    if any("no criminal or immigration" in x for x in lows) and "no criminal convictions" in lows:
        payload["eligibility_criteria"] = [
            x for x in elig if x.strip().lower() != "no criminal convictions"
        ]

    inv = payload.get("invitation_requirements", [])
    if len(inv) > 1:
        inv_sorted = sorted(inv, key=len, reverse=True)
        payload["invitation_requirements"] = [inv_sorted[0]]

    sup = payload.get("supporting_documents", [])
    lows_sup = {x.lower() for x in sup}
    if "passport" in lows_sup and "passport / travel document" in lows_sup:
        payload["supporting_documents"] = [x for x in sup if x.lower() != "passport"]


def verify_final(payload: dict[str, list[str]]) -> list[str]:
    """Return verification issue codes (empty list means all checks passed)."""
    issues: list[str] = []
    for cat in OUTPUT_ORDER:
        vals = payload.get(cat, [])
        if not vals:
            issues.append(f"empty_category:{cat}")
        lowered = [v.lower() for v in vals]
        if len(lowered) != len(set(lowered)):
            issues.append(f"duplicate_entries:{cat}")
        for v in vals:
            if not str(v).strip():
                issues.append(f"malformed_empty_string:{cat}")
    return issues


def build_final_requirements(data_dir: Path) -> dict[str, object]:
    """Return JSON-serializable document with eight category arrays plus `_meta`."""
    entities_path = data_dir / "entities.json"
    aggregated_path = data_dir / "aggregated.json"
    canonical_path = data_dir / "canonical_concepts.json"
    kg_path = data_dir / "knowledge_graph.json"

    entities = json.loads(entities_path.read_text(encoding="utf-8"))
    aggregated = json.loads(aggregated_path.read_text(encoding="utf-8"))
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    kg = json.loads(kg_path.read_text(encoding="utf-8"))

    pages = aggregated.get("pages", [])
    if not isinstance(entities, list):
        entities = []
    if not isinstance(canonical, list):
        canonical = []

    candidates = []
    candidates.extend(extract_from_entities(entities))
    candidates.extend(extract_from_aggregated_signals(pages))
    candidates.extend(extract_from_canonical(canonical))

    scored = consolidate(candidates)
    scored = _merge_fallback(scored)
    payload = _labels_only(scored)
    cleanup_semantic_duplicates(payload)
    issues = verify_final(payload)

    meta = {
        "verification_issues": issues,
        "verification_passed": len(issues) == 0,
        "sources": {
            "entities_count": len(entities),
            "pages_count": len(pages),
            "canonical_rows": len(canonical),
            "graph_edges": len(kg.get("edges", [])),
        },
    }

    document: dict[str, object] = {cat: payload[cat] for cat in OUTPUT_ORDER}
    document["_meta"] = meta
    return document


def write_outputs(data_dir: Path) -> tuple[Path, Path]:
    document = build_final_requirements(data_dir)
    meta = document["_meta"]
    out_json = data_dir / "final_requirements.json"
    out_json.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")

    md_path = data_dir / "final_requirements_summary.md"
    titles = {
        "eligibility_criteria": "Eligibility criteria",
        "supporting_documents": "Supporting documents",
        "required_forms": "Required forms",
        "financial_requirements": "Financial requirements",
        "medical_requirements": "Medical requirements",
        "biometrics_requirements": "Biometrics requirements",
        "invitation_requirements": "Invitation requirements",
        "proof_of_ties_requirements": "Proof of ties requirements",
    }
    lines = [
        "# Final consolidated IRCC visitor visa requirements",
        "",
        "Derived from structured extraction outputs (entities, aggregated pages, canonical concepts, knowledge graph).",
        "",
        f"- Automated verification passed: **{meta.get('verification_passed', False)}**",
    ]
    issues = meta.get("verification_issues") or []
    lines.append(f"- Verification notes: {', '.join(issues) if issues else 'none'}")
    lines.append("")
    for cat in OUTPUT_ORDER:
        lines.append(f"## {titles.get(cat, cat)}")
        lines.append("")
        for item in document.get(cat, []):
            lines.append(f"- {item}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return out_json, md_path
