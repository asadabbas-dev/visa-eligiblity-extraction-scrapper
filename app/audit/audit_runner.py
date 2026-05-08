"""CLI + integration entrypoint for automated audit runs."""

from __future__ import annotations

from pathlib import Path

from app.audit.dataset_auditor import DatasetAuditor
from app.audit.final_report_generator import FinalReportGenerator


def run_audit(data_dir: Path) -> dict:
    auditor = DatasetAuditor(data_dir=data_dir)
    payload = auditor.run()
    generator = FinalReportGenerator(data_dir=data_dir)
    return generator.generate(payload)


def main() -> None:
    report = run_audit(Path("data"))
    print(
        f"AUDIT STATUS={report['system_status']} "
        f"COVERAGE={report['coverage_percent']} "
        f"CONFIDENCE={report['confidence_score']}"
    )


if __name__ == "__main__":
    main()
