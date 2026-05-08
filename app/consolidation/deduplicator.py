"""Semantic deduplication keys for merging synonymous requirement phrases."""

from __future__ import annotations

import re

# Within-category dedupe: multiple raw slugs → one stable key before display formatting.
FINANCIAL_SYNONYMS: frozenset[str] = frozenset(
    {"proof_of_funds", "bank_statements", "fees"}
)


def normalize_entity_concept(concept: str) -> str:
    """Normalize entity concept string to snake_case slug."""
    s = concept.strip().lower().replace("-", "_")
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def financial_canonical_slug(slug: str) -> str:
    """Collapse financial synonyms to one key."""
    if slug in FINANCIAL_SYNONYMS:
        return "proof_of_funds"
    return slug


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """Remove duplicate strings preserving first occurrence order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out
