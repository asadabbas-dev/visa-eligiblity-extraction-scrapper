# IRCC Visitor Visa — Crawler, Extraction, QA, and Consolidation

Production-grade Python pipeline that crawls IRCC visitor-visa–related pages on `canada.ca` / `ircc.canada.ca`, extracts structured immigration content, runs validation and auditing, enriches entities into a knowledge graph, and produces **final consolidated requirement lists** for downstream AI, search, or automation.

## Capabilities

### Crawling

- BFS traversal with queue, visited set, depth/page limits
- URL normalization (drops fragments; skips `mailto:` / `javascript:`)
- Domain restriction and optional **path prefix allowlist** (visitor-visa–focused defaults)
- Retries, timeouts, rate limiting, structured logging
- **robots.txt** handling (via `requests`; configurable fail-open on fetch errors)

### Scraping and extraction

- Semantic heading-based extraction (`h1` / `h2` / `h3`), hierarchy preservation
- Sections classified into immigration-themed buckets (keyword + semantic groups)
- Page signals for eligibility and supporting documents
- Tables, bullets, PDF links, internal links
- HTML cleanup (main content, nav/footer noise reduction)
- Optional PDF download and text extraction (`pdfplumber`)

### Intelligence layer

- Canonical concept mapping and entity extraction with confidence scores
- Knowledge graph (concepts + co-occurrence edges)
- Outputs: `entities.json`, `canonical_concepts.json`, `knowledge_graph.json`, `extraction_confidence_report.json`

### Validation and QA

- Coverage vs gold expectations, quality metrics, missing-requirements report
- Outputs: `validation_report.json`, `quality_metrics.json`, `missing_requirements.json`

### Auditing

- Automated verification of critical concepts, hierarchy checks, output integrity
- PASS / WARNING / FAIL style outcome with recommendations
- Outputs: `final_audit_report.json`, `final_audit_summary.md`
- Standalone: `python -m app.audit.audit_runner` (uses `data/` by default)

### Requirement consolidation

- Merges entities, aggregates, canonical concepts, and graph signals into **deduplicated, human-readable requirement buckets**
- Outputs: **`final_requirements.json`**, **`final_requirements_summary.md`**

Client-facing narrative docs (optional) live under `data/`, for example `client_delivery_report.md` and `client_eligibility_supporting_docs_report.md`.

---

## Project layout

```text
├── app/
│   ├── crawler/           # BFS, queue, URLs, robots
│   ├── scraper/           # Scraper, extractor, classifier, cleaner
│   ├── parsers/           # HTML + PDF
│   ├── storage/           # JSON persistence
│   ├── validation/        # Coverage and quality reports
│   ├── intelligence/      # Concepts, entities, knowledge graph
│   ├── audit/             # Automated audit and final client audit JSON/MD
│   ├── consolidation/     # final_requirements.json builder
│   ├── utils/             # Settings, logging, constants
│   └── main.py            # End-to-end pipeline entrypoint
├── data/                  # Generated outputs (see below)
├── logs/                  # Rotating logs
├── tests/                 # Unit tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Seed URLs

Configured in `app/main.py` (edit there to change scope):

- [Visitor visa (about)](https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/visitor-visa.html)
- [How to apply (visitor visa)](https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/apply-visitor-visa.html)
- [Eligibility](https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/eligibility.html)
- [Common supporting documents](https://www.canada.ca/en/immigration-refugees-citizenship/services/application/common-supporting-documents.html)
- [Guide 5256 (visitor visa / TRV, paper)](https://www.canada.ca/en/immigration-refugees-citizenship/services/application/application-forms-guides/guide-5256-applying-visitor-visa-temporary-resident-visa.html)

---

## Setup

Python **3.12+** recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAX_DEPTH` | `2` | Max BFS depth |
| `MAX_PAGES` | `120` | Max URLs discovered |
| `REQUEST_TIMEOUT` | `20` | HTTP timeout (seconds) |
| `REQUEST_RETRIES` | `3` | Retry count for transient failures |
| `RATE_LIMIT_SECONDS` | `0.8` | Delay between requests |
| `WORKERS` | `6` | Thread pool size for scraping |
| `OBEY_ROBOTS` | `true` | Honor robots.txt |
| `ROBOTS_FAIL_OPEN` | `true` | If robots fetch fails, continue (fail-closed if `false`) |
| `CRAWL_PATH_ALLOWLIST` | *(see `Settings` in `app/utils/helpers.py`)* | Comma-separated path prefixes; only URLs whose path starts with one prefix are enqueued |
| `EXTRACT_PDF_TEXT` | `false` | Extract text from linked PDFs |
| `DOWNLOAD_PDFS` | `false` | Save PDFs under `data/pdfs/` |
| `DATA_DIR` | `data` | Output directory |
| `LOGS_DIR` | `logs` | Log directory |

Example:

```bash
export MAX_DEPTH=2
export MAX_PAGES=120
export RATE_LIMIT_SECONDS=1.0
export EXTRACT_PDF_TEXT=true
```

On macOS, if HTTPS verification fails for Python, install certificates from your Python installer or set `ROBOTS_FAIL_OPEN=true` while diagnosing.

---

## Run the full pipeline

From the repository root:

```bash
python -m app.main
```

This runs, in order: crawl → scrape → per-page + aggregated JSON → validation → intelligence artifacts → **audit** → **`final_requirements.json`** + **`final_requirements_summary.md`**.

---

## Output files (`DATA_DIR`, usually `data/`)

| Artifact | Description |
|----------|-------------|
| `pages/*.json` | One structured record per crawled page |
| `aggregated.json` | All pages combined |
| `metadata/crawl_metadata.json` | Crawl statistics |
| `validation_report.json` | Coverage by expected concept groups |
| `quality_metrics.json` | Aggregate quality scores |
| `missing_requirements.json` | Gaps vs expectations |
| `entities.json` | Extracted entities + confidence |
| `canonical_concepts.json` | Concept frequencies and URLs |
| `knowledge_graph.json` | Nodes, edges, grouped entities |
| `extraction_confidence_report.json` | Confidence breakdown |
| `final_audit_report.json` | Audit verdict and checks |
| `final_audit_summary.md` | Human-readable audit |
| **`final_requirements.json`** | **Consolidated eligibility, docs, forms, financial/medical/biometrics/invitation/ties** |
| **`final_requirements_summary.md`** | Same as Markdown |

Logs: `logs/crawler.log` (rotating).

Sample fixture (not overwritten by pipeline unless you replace it): `data/sample_output.json`.

---

## Auxiliary commands

**Audit only** (after `data/` is populated):

```bash
python -m app.audit.audit_runner
```

**Regenerate final requirements only** (after intelligence outputs exist):

```bash
python -c "from pathlib import Path; from app.consolidation.final_json_builder import write_outputs; write_outputs(Path('data'))"
```

---

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## Git

A `.gitignore` is included for virtualenvs, caches, logs, and common secrets. Uncomment optional lines there if you prefer not to commit large generated `data/` blobs.

---

## Compliance and operations

- Restrict crawling to **`canada.ca`** and **`ircc.canada.ca`** (see crawler configuration).
- Respect **robots.txt** in production (`OBEY_ROBOTS=true`).
- Use conservative **rate limits**; IRCC pages are public service infrastructure.

---

## Extensibility

- Swap keyword classification in `app/scraper/classifier.py` for embeddings or an ML model.
- Add French (`fr`) seeds and language-aware normalization.
- Persist crawl frontier in Redis/RabbitMQ for very large crawls.
- Store snapshots or hashes of pages to detect template changes.

---

## Disclaimer

This tool assists with **structuring publicly published IRCC web content**. It is **not** legal advice. Users must confirm requirements against current official IRCC instructions and their own application checklist.
