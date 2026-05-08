"""Hierarchy integrity checks over extracted page structures."""

from __future__ import annotations


class HierarchyVerifier:
    """Validates h2/h3 hierarchy presence and inheritance consistency."""

    def verify(self, aggregated_payload: dict) -> dict:
        pages = aggregated_payload.get("pages", [])
        total_pages = len(pages)
        pages_with_hierarchy = 0
        h3_with_parent = 0
        total_h3 = 0
        total_nodes = 0
        non_empty_nodes = 0

        def walk(nodes: list[dict], parent: str | None = None) -> None:
            nonlocal h3_with_parent, total_h3, total_nodes, non_empty_nodes
            for node in nodes:
                total_nodes += 1
                items = node.get("items", [])
                bullets = node.get("bullets", [])
                tables = node.get("tables", [])
                if items or bullets or tables:
                    non_empty_nodes += 1
                level = str(node.get("level", ""))
                if level == "h3":
                    total_h3 += 1
                    if node.get("parent_heading"):
                        h3_with_parent += 1
                walk(node.get("children", []), node.get("heading"))

        for page in pages:
            hierarchy = page.get("hierarchy", [])
            if hierarchy:
                pages_with_hierarchy += 1
                walk(hierarchy)

        hierarchy_presence = (pages_with_hierarchy / max(1, total_pages) * 100.0)
        h3_inheritance = (h3_with_parent / max(1, total_h3) * 100.0)
        completeness = (non_empty_nodes / max(1, total_nodes) * 100.0)
        integrity = (0.4 * hierarchy_presence) + (0.4 * h3_inheritance) + (0.2 * completeness)

        return {
            "hierarchy_pages_percent": round(hierarchy_presence, 2),
            "h3_parent_inheritance_percent": round(h3_inheritance, 2),
            "hierarchy_content_completeness_percent": round(completeness, 2),
            "hierarchy_integrity_percent": round(integrity, 2),
        }
