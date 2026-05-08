"""Output JSON/schema integrity checker."""

from __future__ import annotations

import json
from pathlib import Path


class OutputIntegrityChecker:
    """Checks JSON validity, schema presence, and malformed records."""

    REQUIRED_FILES: tuple[str, ...] = (
        "aggregated.json",
        "entities.json",
        "canonical_concepts.json",
        "knowledge_graph.json",
        "extraction_confidence_report.json",
    )

    def _load_json(self, path: Path) -> tuple[bool, dict | list | None, str | None]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return True, payload, None
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return False, None, str(exc)

    def check(self, data_dir: Path) -> dict:
        missing_files = []
        invalid_json = {}
        malformed_entities = 0
        empty_sections = 0
        schema_issues: list[str] = []

        payloads: dict[str, dict | list] = {}
        for filename in self.REQUIRED_FILES:
            path = data_dir / filename
            if not path.exists():
                missing_files.append(filename)
                continue
            valid, payload, error = self._load_json(path)
            if not valid:
                invalid_json[filename] = error
                continue
            if payload is not None:
                payloads[filename] = payload

        aggregated = payloads.get("aggregated.json", {})
        if isinstance(aggregated, dict):
            pages = aggregated.get("pages")
            if not isinstance(pages, list):
                schema_issues.append("aggregated.pages missing or not list")
            else:
                for page in pages:
                    if not isinstance(page, dict):
                        continue
                    for key in ("url", "page_title", "sections"):
                        if key not in page:
                            schema_issues.append(f"page missing key: {key}")
                    if isinstance(page.get("sections"), list):
                        for section in page["sections"]:
                            if not isinstance(section, dict):
                                continue
                            if not section.get("heading"):
                                schema_issues.append("section missing heading")
                            if not (section.get("items") or section.get("bullets") or section.get("tables")):
                                empty_sections += 1

        entities = payloads.get("entities.json", [])
        if isinstance(entities, list):
            required_entity_keys = {"concept", "confidence", "source_heading", "source_url", "source_type", "category"}
            for entity in entities:
                if not isinstance(entity, dict) or not required_entity_keys.issubset(entity.keys()):
                    malformed_entities += 1

        critical_schema_failures = bool(missing_files or invalid_json)
        return {
            "missing_files": missing_files,
            "invalid_json": invalid_json,
            "schema_issues": sorted(set(schema_issues)),
            "empty_sections": empty_sections,
            "malformed_entities": malformed_entities,
            "critical_schema_failures": critical_schema_failures,
        }
