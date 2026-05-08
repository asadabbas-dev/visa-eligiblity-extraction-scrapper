"""Final PASS/WARNING/FAIL report generation."""

from __future__ import annotations

import json
from pathlib import Path


class FinalReportGenerator:
    """Builds machine + human readable audit reports."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def _decision(self, coverage: float, confidence: float, hierarchy: float, relationship: float, schema_fail: bool) -> str:
        if schema_fail:
            return "FAIL"
        if coverage > 90 and hierarchy > 80 and relationship > 80:
            return "PASS"
        if coverage < 70 or hierarchy < 50 or relationship < 50:
            return "FAIL"
        return "WARNING"

    def generate(self, audit_payload: dict) -> dict:
        extraction = audit_payload["extraction_verification"]
        coverage = audit_payload["coverage_audit"]
        hierarchy = audit_payload["hierarchy_integrity"]
        relationships = audit_payload["relationship_integrity"]
        integrity = audit_payload["output_integrity"]

        coverage_percent = float(extraction.get("coverage_percent", 0.0))
        confidence_score = float(coverage.get("confidence_quality_score", 0.0))
        hierarchy_integrity = float(hierarchy.get("hierarchy_integrity_percent", 0.0))
        relationship_integrity = float(relationships.get("relationship_integrity_percent", 0.0))
        status = self._decision(
            coverage_percent,
            confidence_score,
            hierarchy_integrity,
            relationship_integrity,
            bool(integrity.get("critical_schema_failures", False)),
        )

        weak_areas = []
        if coverage.get("missing_concepts"):
            weak_areas.append("critical concept coverage gaps")
        if coverage.get("low_confidence_categories"):
            weak_areas.append("low confidence categories")
        if hierarchy_integrity < 80:
            weak_areas.append("hierarchy integrity below target")
        if relationship_integrity < 80:
            weak_areas.append("relationship integrity below target")
        if integrity.get("schema_issues"):
            weak_areas.append("schema consistency issues")

        recommendations = []
        if extraction["missing_critical_concepts"]:
            recommendations.append("Expand concept variants and section extraction rules for missing concepts.")
        if coverage["confidence_distribution"]["lt_0_5"] > 0:
            recommendations.append("Tune confidence scoring and evidence filtering for low-confidence entities.")
        if hierarchy_integrity < 80:
            recommendations.append("Increase DOM hierarchy parsing depth and inheritance handling.")
        if relationship_integrity < 80:
            recommendations.append("Add graph edge rules for required immigration concept relationships.")
        if integrity["critical_schema_failures"]:
            recommendations.append("Fix missing/invalid output files before using dataset for AI.")

        final = {
            "system_status": status,
            "coverage_percent": round(coverage_percent, 2),
            "confidence_score": round(confidence_score, 2),
            "missing_critical_concepts": extraction["missing_critical_concepts"],
            "weak_areas": weak_areas,
            "verified_concepts": sorted(
                concept for groups in extraction["found_by_group"].values() for concept in groups
            ),
            "relationship_integrity": relationships,
            "hierarchy_integrity": hierarchy,
            "recommendations": recommendations,
            "entity_trust_score": coverage.get("entity_trust_score", 0.0),
            "confidence_distribution": coverage.get("confidence_distribution", {}),
        }

        json_path = self.data_dir / "final_audit_report.json"
        json_path.write_text(json.dumps(final, indent=2), encoding="utf-8")

        ai_ready = "Yes" if status == "PASS" else "Not yet"
        recommendation_lines = [f"- {rec}" for rec in final["recommendations"]]
        if not recommendation_lines:
            recommendation_lines = ["- No critical recommendations."]
        md_path = self.data_dir / "final_audit_summary.md"
        md_path.write_text(
            "\n".join(
                [
                    "# Final Audit Summary",
                    "",
                    f"- **System status:** {status}",
                    f"- **Coverage percent:** {final['coverage_percent']}%",
                    f"- **Confidence score:** {final['confidence_score']}",
                    f"- **Entity trust score:** {final['entity_trust_score']}",
                    "",
                    "## What Works",
                    f"- Required concepts verified: {len(final['verified_concepts'])}",
                    f"- Hierarchy integrity: {hierarchy_integrity}%",
                    f"- Relationship integrity: {relationship_integrity}%",
                    "",
                    "## What Is Missing",
                    f"- Missing critical concepts: {', '.join(final['missing_critical_concepts']) or 'None'}",
                    f"- Weak areas: {', '.join(final['weak_areas']) or 'None'}",
                    "",
                    "## Quality Assessment",
                    f"- Extraction quality: {'Strong' if final['coverage_percent'] >= 90 else 'Needs improvement'}",
                    f"- Confidence quality: {'Strong' if final['confidence_score'] >= 70 else 'Needs improvement'}",
                    "",
                    "## AI Readiness",
                    f"- AI-ready dataset: {ai_ready}",
                    "- Immigration requirement extraction status: "
                    + ("Successful" if not final["missing_critical_concepts"] else "Partially successful"),
                    "",
                    "## Recommendations",
                    *recommendation_lines,
                    "",
                ]
            ),
            encoding="utf-8",
        )

        return final
