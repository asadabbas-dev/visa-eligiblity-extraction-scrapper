"""Application entrypoint for IRCC crawler + scraper pipeline."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from app.audit.audit_runner import run_audit
from app.consolidation.final_json_builder import write_outputs
from app.crawler.crawler import BFSCrawler
from app.intelligence.concept_mapper import CANONICAL_CONCEPT_VARIANTS, CanonicalConceptMapper
from app.intelligence.entity_extractor import EntityExtractor
from app.intelligence.knowledge_graph_builder import KnowledgeGraphBuilder
from app.scraper.scraper import IRCCScraper
from app.storage.json_storage import CrawlMetadata, JSONStorage
from app.utils.helpers import Settings
from app.utils.logger import setup_logger
from app.validation.validator import DatasetValidator


SEED_URLS: list[str] = [
    "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/visitor-visa.html",
    "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/apply-visitor-visa.html",
    "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/eligibility.html",
    "https://www.canada.ca/en/immigration-refugees-citizenship/services/application/common-supporting-documents.html",
    "https://www.canada.ca/en/immigration-refugees-citizenship/services/application/application-forms-guides/guide-5256-applying-visitor-visa-temporary-resident-visa.html",
]


def run() -> None:
    settings = Settings()
    logger = setup_logger(settings.logs_dir)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    crawler = BFSCrawler(
        settings=settings,
        logger=logger,
        allowed_domains={"canada.ca", "ircc.canada.ca"},
    )
    scraper = IRCCScraper(settings=settings, logger=logger)
    storage = JSONStorage(output_dir=settings.data_dir)

    crawl_result = crawler.crawl(start_urls=SEED_URLS)
    logger.info("Discovered %s URLs", len(crawl_result.discovered_urls))

    pages = []
    with ThreadPoolExecutor(max_workers=settings.workers) as pool:
        future_map = {pool.submit(scraper.scrape_page, url): url for url in crawl_result.discovered_urls}
        for future in as_completed(future_map):
            page_data = future.result()
            if not page_data:
                continue
            storage.save_page(page_data)
            pages.append(page_data)

    storage.save_aggregate(pages)
    storage.save_metadata(
        CrawlMetadata(
            seed_urls=SEED_URLS,
            total_discovered_urls=len(crawl_result.discovered_urls),
            total_scraped_pages=len(pages),
            skipped_by_robots=crawl_result.skipped_by_robots,
            failed_requests=crawl_result.failed_requests,
            generated_at=storage.now_iso(),
        )
    )
    validator = DatasetValidator(data_dir=settings.data_dir)
    reports = validator.generate_reports()
    logger.info(
        "Validation reports generated: %s, %s, %s",
        reports.validation_report_path,
        reports.quality_metrics_path,
        reports.missing_requirements_path,
    )
    aggregated_payload = json.loads((settings.data_dir / "aggregated.json").read_text(encoding="utf-8"))
    pages_payload = aggregated_payload.get("pages", [])

    concept_mapper = CanonicalConceptMapper(CANONICAL_CONCEPT_VARIANTS)
    entity_extractor = EntityExtractor()
    kg_builder = KnowledgeGraphBuilder()

    entities = entity_extractor.extract(pages_payload)
    entities_path = settings.data_dir / "entities.json"
    entities_path.write_text(
        json.dumps([entity.to_dict() for entity in entities], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    canonical_concepts: dict[str, dict] = {}
    for page in pages_payload:
        url = page.get("url", "")
        text_parts: list[str] = []
        for section in page.get("sections", []):
            text_parts.append(section.get("heading", ""))
            text_parts.extend(section.get("items", []))
            text_parts.extend(section.get("bullets", []))
        text = " ".join(text_parts)
        for concept in concept_mapper.match_concepts(text):
            row = canonical_concepts.setdefault(concept, {"concept": concept, "urls": set(), "occurrences": 0})
            row["urls"].add(url)
            row["occurrences"] += 1
    canonical_path = settings.data_dir / "canonical_concepts.json"
    canonical_path.write_text(
        json.dumps(
            [
                {
                    "concept": value["concept"],
                    "occurrences": value["occurrences"],
                    "urls": sorted(value["urls"]),
                }
                for value in sorted(canonical_concepts.values(), key=lambda item: item["concept"])
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    knowledge_graph_path = settings.data_dir / "knowledge_graph.json"
    knowledge_graph_path.write_text(
        json.dumps(kg_builder.build(entities), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    confidence_report = {
        "entity_count": len(entities),
        "average_confidence": round(
            sum(entity.confidence for entity in entities) / len(entities), 4
        )
        if entities
        else 0.0,
        "high_confidence_entities": len([entity for entity in entities if entity.confidence >= 0.85]),
        "medium_confidence_entities": len([entity for entity in entities if 0.65 <= entity.confidence < 0.85]),
        "low_confidence_entities": len([entity for entity in entities if entity.confidence < 0.65]),
        "by_source_type": {
            source_type: len([entity for entity in entities if entity.source_type == source_type])
            for source_type in {"paragraph", "bullet", "table", "pdf"}
        },
    }
    confidence_path = settings.data_dir / "extraction_confidence_report.json"
    confidence_path.write_text(json.dumps(confidence_report, indent=2), encoding="utf-8")
    logger.info(
        "Intelligence outputs generated: %s, %s, %s, %s",
        entities_path,
        canonical_path,
        knowledge_graph_path,
        confidence_path,
    )
    audit_report = run_audit(settings.data_dir)
    logger.info(
        "Final audit generated: status=%s coverage=%s confidence=%s",
        audit_report["system_status"],
        audit_report["coverage_percent"],
        audit_report["confidence_score"],
    )
    req_json, req_md = write_outputs(settings.data_dir)
    logger.info("Final requirements consolidated: %s, %s", req_json, req_md)
    logger.info("Pipeline completed. Scraped pages: %s", len(pages))


if __name__ == "__main__":
    run()
