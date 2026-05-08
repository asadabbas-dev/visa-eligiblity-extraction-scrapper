"""Builds a deterministic knowledge graph from extracted entities."""

from __future__ import annotations

from dataclasses import dataclass

from app.intelligence.entity_extractor import ExtractedEntity


@dataclass(slots=True)
class KnowledgeGraphBuilder:
    """Constructs concept graph nodes/edges and grouped entities."""

    def build(self, entities: list[ExtractedEntity]) -> dict:
        nodes: dict[str, dict] = {}
        edges: dict[tuple[str, str, str], int] = {}

        for entity in entities:
            node = nodes.setdefault(
                entity.concept,
                {"id": entity.concept, "type": "concept", "categories": set(), "sources": set()},
            )
            node["categories"].add(entity.category)
            node["sources"].add(entity.source_url)

        by_source_heading: dict[tuple[str, str], list[ExtractedEntity]] = {}
        for entity in entities:
            key = (entity.source_url, entity.source_heading)
            by_source_heading.setdefault(key, []).append(entity)

        for grouped in by_source_heading.values():
            concepts = sorted({entity.concept for entity in grouped})
            for idx in range(len(concepts)):
                for jdx in range(idx + 1, len(concepts)):
                    edge_key = (concepts[idx], "related_to", concepts[jdx])
                    edges[edge_key] = edges.get(edge_key, 0) + 1

        serialized_nodes = [
            {
                **node,
                "categories": sorted(node["categories"]),
                "sources": sorted(node["sources"]),
            }
            for node in nodes.values()
        ]
        serialized_edges = [
            {"source": source, "relation": relation, "target": target, "weight": weight}
            for (source, relation, target), weight in edges.items()
        ]

        grouped_entities = {
            "document_requirements": sorted(
                {e.concept for e in entities if e.category in {"supporting_documents", "required_forms"}}
            ),
            "eligibility_requirements": sorted(
                {e.concept for e in entities if e.category in {"eligibility_criteria", "financial_requirements"}}
            ),
            "forms": sorted({e.concept for e in entities if e.concept.startswith("imm_")}),
            "fees": sorted({e.concept for e in entities if e.concept == "fees"}),
            "biometrics": sorted({e.concept for e in entities if e.concept == "biometrics"}),
        }
        return {"nodes": serialized_nodes, "edges": serialized_edges, "entities": grouped_entities}
