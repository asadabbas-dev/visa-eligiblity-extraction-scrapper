"""Tests for automated auditing system."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.audit.audit_runner import run_audit


class TestAuditSystem(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self._write_fixture_files()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write(self, name: str, payload: dict | list) -> None:
        (self.data_dir / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_fixture_files(self) -> None:
        self._write(
            "aggregated.json",
            {
                "pages": [
                    {
                        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/eligibility.html",
                        "page_title": "Eligibility",
                        "eligibility_signals": ["good health", "possible medical exam"],
                        "supporting_document_signals": ["bank statements", "proof of relationship"],
                        "sections": [
                            {"heading": "Eligibility", "items": ["good health"], "bullets": [], "tables": []}
                        ],
                        "hierarchy": [
                            {
                                "heading": "Eligibility",
                                "level": "h2",
                                "items": ["good health"],
                                "bullets": [],
                                "tables": [],
                                "children": [
                                    {
                                        "heading": "Medical",
                                        "level": "h3",
                                        "items": ["medical exam"],
                                        "bullets": [],
                                        "tables": [],
                                        "children": [],
                                        "parent_heading": "Eligibility",
                                    }
                                ],
                                "parent_heading": None,
                            }
                        ],
                    }
                ],
                "count": 1,
            },
        )
        self._write(
            "entities.json",
            [
                {
                    "concept": "passport",
                    "confidence": 0.72,
                    "source_heading": "Eligibility",
                    "source_url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/eligibility.html",
                    "source_type": "bullet",
                    "category": "eligibility_criteria",
                    "evidence": "passport",
                },
                {
                    "concept": "bank_statements",
                    "confidence": 0.81,
                    "source_heading": "Documents",
                    "source_url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/application/common-supporting-documents.html",
                    "source_type": "bullet",
                    "category": "supporting_documents",
                    "evidence": "bank statement",
                },
                {
                    "concept": "biometrics",
                    "confidence": 0.66,
                    "source_heading": "Biometrics",
                    "source_url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/visitor-visa.html",
                    "source_type": "paragraph",
                    "category": "biometrics",
                    "evidence": "biometric fee",
                },
            ],
        )
        self._write(
            "canonical_concepts.json",
            [
                {"concept": "passport", "occurrences": 1, "urls": ["https://www.canada.ca/a"]},
                {"concept": "bank_statements", "occurrences": 1, "urls": ["https://www.canada.ca/b"]},
                {"concept": "biometrics", "occurrences": 1, "urls": ["https://www.canada.ca/c"]},
                {"concept": "imm_5476", "occurrences": 1, "urls": ["https://www.canada.ca/d"]},
            ],
        )
        self._write(
            "knowledge_graph.json",
            {
                "nodes": [
                    {"id": "passport"},
                    {"id": "bank_statements"},
                    {"id": "proof_of_funds"},
                    {"id": "biometrics"},
                    {"id": "visitor_visa"},
                ],
                "edges": [
                    {"source": "proof_of_funds", "relation": "related_to", "target": "bank_statements", "weight": 1},
                    {"source": "visitor_visa", "relation": "related_to", "target": "passport", "weight": 1},
                    {"source": "biometrics", "relation": "related_to", "target": "visitor_visa", "weight": 1},
                ],
            },
        )
        self._write("extraction_confidence_report.json", {"entity_count": 3})

    def test_audit_runner_generates_reports(self) -> None:
        result = run_audit(self.data_dir)
        self.assertIn(result["system_status"], {"PASS", "WARNING", "FAIL"})
        self.assertTrue((self.data_dir / "final_audit_report.json").exists())
        self.assertTrue((self.data_dir / "final_audit_summary.md").exists())
        report = json.loads((self.data_dir / "final_audit_report.json").read_text(encoding="utf-8"))
        self.assertIn("coverage_percent", report)
        self.assertIn("relationship_integrity", report)
        self.assertIn("hierarchy_integrity", report)


if __name__ == "__main__":
    unittest.main()
