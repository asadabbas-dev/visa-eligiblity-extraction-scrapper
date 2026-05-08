"""Hierarchical DOM-aware section parsing models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class HierarchyNode:
    """Represents an h2/h3 section with nested semantic context."""

    heading: str
    level: str
    items: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    tables: list[list[dict[str, str]]] = field(default_factory=list)
    children: list["HierarchyNode"] = field(default_factory=list)
    parent_heading: str | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["children"] = [child.to_dict() for child in self.children]
        return payload


class HierarchyParser:
    """Builds a heading hierarchy from extracted section payloads."""

    def build_tree(self, sections: list[dict]) -> list[HierarchyNode]:
        roots: list[HierarchyNode] = []
        current_h2: HierarchyNode | None = None

        for section in sections:
            node = HierarchyNode(
                heading=section.get("heading", ""),
                level=section.get("heading_level", ""),
                items=section.get("items", []),
                bullets=section.get("bullets", []),
                tables=section.get("tables", []),
            )
            if node.level == "h2":
                roots.append(node)
                current_h2 = node
            elif node.level == "h3":
                if current_h2:
                    node.parent_heading = current_h2.heading
                    current_h2.children.append(node)
                else:
                    roots.append(node)
            else:
                roots.append(node)
        return roots
