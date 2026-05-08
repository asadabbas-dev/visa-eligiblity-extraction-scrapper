"""Knowledge graph relationship integrity verification."""

from __future__ import annotations


class RelationshipVerifier:
    """Validates required relations and detects orphan concepts."""

    REQUIRED_RELATIONS: tuple[tuple[str, str], ...] = (
        ("proof_of_funds", "bank_statements"),
        ("visitor_visa", "passport"),
        ("biometrics", "visitor_visa"),
    )

    def verify(self, knowledge_graph: dict, discovered_concepts: set[str]) -> dict:
        nodes = knowledge_graph.get("nodes", [])
        edges = knowledge_graph.get("edges", [])

        graph_nodes = {str(node.get("id", "")).lower() for node in nodes if node.get("id")}
        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            source = str(edge.get("source", "")).lower()
            target = str(edge.get("target", "")).lower()
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set()).add(source)

        relation_checks: list[dict] = []
        passed = 0
        for source, target in self.REQUIRED_RELATIONS:
            source_n = source.lower()
            target_n = target.lower()
            exists = target_n in adjacency.get(source_n, set())
            relation_checks.append({"source": source_n, "target": target_n, "exists": exists})
            if exists:
                passed += 1

        orphan_concepts = sorted(
            concept for concept in (discovered_concepts & graph_nodes) if concept not in adjacency
        )
        integrity = (passed / len(self.REQUIRED_RELATIONS) * 100.0) if self.REQUIRED_RELATIONS else 100.0
        return {
            "required_relationship_checks": relation_checks,
            "relationship_integrity_percent": round(integrity, 2),
            "orphan_concepts": orphan_concepts,
            "graph_node_count": len(graph_nodes),
            "graph_edge_count": len(edges),
        }
