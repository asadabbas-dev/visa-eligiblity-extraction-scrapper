"""Dataset-level audit orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from app.audit.concept_coverage_checker import ConceptCoverageChecker
from app.audit.extraction_verifier import ExtractionVerifier, normalize_concept
from app.audit.hierarchy_verifier import HierarchyVerifier
from app.audit.output_integrity_checker import OutputIntegrityChecker
from app.audit.relationship_verifier import RelationshipVerifier


class DatasetAuditor:
    """Runs all audit dimensions and returns consolidated findings."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.extraction_verifier = ExtractionVerifier()
        self.coverage_checker = ConceptCoverageChecker()
        self.relationship_verifier = RelationshipVerifier()
        self.hierarchy_verifier = HierarchyVerifier()
        self.integrity_checker = OutputIntegrityChecker()

    def _load_json(self, name: str) -> dict | list:
        return json.loads((self.data_dir / name).read_text(encoding="utf-8"))

    def _discover_concepts(self, entities: list[dict], canonical: list[dict], graph: dict, aggregated: dict) -> set[str]:
        discovered = {
            normalize_concept(str(entity.get("concept", "")))
            for entity in entities
            if entity.get("concept")
        }
        discovered.update(
            normalize_concept(str(item.get("concept", "")))
            for item in canonical
            if isinstance(item, dict) and item.get("concept")
        )
        discovered.update(
            normalize_concept(str(node.get("id", "")))
            for node in graph.get("nodes", [])
            if isinstance(node, dict) and node.get("id")
        )
        for page in aggregated.get("pages", []):
            discovered.update(normalize_concept(value) for value in page.get("eligibility_signals", []))
            discovered.update(normalize_concept(value) for value in page.get("supporting_document_signals", []))
        if "possible_medical_exam" in discovered:
            discovered.add("medical_exam")
        if "imm_5257" in discovered:
            discovered.add("imm5257")
        if "imm_5645" in discovered:
            discovered.add("imm5645")
        if "imm_5476" in discovered:
            discovered.add("imm5476")
        return {concept for concept in discovered if concept}

    def run(self) -> dict:
        integrity = self.integrity_checker.check(self.data_dir)
        aggregated = self._load_json("aggregated.json") if not integrity["missing_files"] else {"pages": []}
        entities = self._load_json("entities.json") if not integrity["missing_files"] else []
        canonical = self._load_json("canonical_concepts.json") if not integrity["missing_files"] else []
        graph = self._load_json("knowledge_graph.json") if not integrity["missing_files"] else {"nodes": [], "edges": []}
        entities_list = entities if isinstance(entities, list) else []
        canonical_list = canonical if isinstance(canonical, list) else []
        aggregated_dict = aggregated if isinstance(aggregated, dict) else {"pages": []}
        graph_dict = graph if isinstance(graph, dict) else {"nodes": [], "edges": []}

        discovered = self._discover_concepts(entities_list, canonical_list, graph_dict, aggregated_dict)
        extraction = self.extraction_verifier.verify(discovered)
        coverage = self.coverage_checker.analyze(entities_list, extraction["missing_critical_concepts"])
        hierarchy = self.hierarchy_verifier.verify(aggregated_dict)
        relationships = self.relationship_verifier.verify(graph_dict, discovered)

        return {
            "extraction_verification": extraction,
            "coverage_audit": coverage,
            "relationship_integrity": relationships,
            "hierarchy_integrity": hierarchy,
            "output_integrity": integrity,
        }
