# IRCC Visitor Visa Crawler + Scraper + Structured Extraction Engine

Production-grade Python system for crawling IRCC visitor visa pages, extracting semantic immigration data, classifying content into domain categories, and storing normalized JSON outputs for AI/search/automation pipelines.

## Features

- BFS crawler with queue management, visited set, URL normalization, depth limits, domain restrictions, retries, timeout, rate limiting, and robots.txt compliance
- Semantic heading-based extraction (`h1`/`h2`/`h3`) that associates content under each section
- Extracts:
  - page title, URL, headings
  - eligibility criteria
  - supporting documents
  - required forms (IMM references)
  - application steps
  - fees/processing info (when present)
  - bullet points, tables
  - PDF links and IRCC internal links
- Cleaner for whitespace/unicode normalization and deduplication
- Extensible keyword-based classifier (ready for future NLP/ML model integration)
- JSON storage:
  - one JSON per page
  - aggregated JSON
  - crawl metadata JSON
- Optional PDF downloading and extraction via `pdfplumber`
- Concurrent scraping for scale

## Project Structure

```text
project/
├── app/
│   ├── crawler/
│   │   ├── crawler.py
│   │   ├── queue_manager.py
│   │   ├── url_manager.py
│   │   └── robots.py
│   ├── scraper/
│   │   ├── scraper.py
│   │   ├── extractor.py
│   │   ├── classifier.py
│   │   └── cleaner.py
│   ├── parsers/
│   │   ├── html_parser.py
│   │   └── pdf_parser.py
│   ├── storage/
│   │   ├── json_storage.py
│   │   └── file_manager.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── helpers.py
│   │   └── constants.py
│   └── main.py
├── data/
├── logs/
├── requirements.txt
└── README.md
```

## Seed URLs

Configured in `app/main.py`:

- <https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/visitor-visa.html>
- <https://www.canada.ca/en/immigration-refugees-citizenship/services/application/application-forms-guides/application-visitor-visa-temporary-resident-visa.html>
- <https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/eligibility.html>
- <https://www.canada.ca/en/immigration-refugees-citizenship/services/application/common-supporting-documents.html>

## Setup Instructions

1. Create and activate virtual environment:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration (Environment Variables)

- `MAX_DEPTH` (default: `2`): BFS crawl depth limit
- `MAX_PAGES` (default: `120`): max discovered pages
- `REQUEST_TIMEOUT` (default: `20`): HTTP timeout in seconds
- `REQUEST_RETRIES` (default: `3`): retries for transient errors
- `RATE_LIMIT_SECONDS` (default: `0.8`): delay between requests
- `WORKERS` (default: `6`): thread workers for scraping
- `OBEY_ROBOTS` (default: `true`): respect robots.txt rules
- `EXTRACT_PDF_TEXT` (default: `false`): parse PDF text with pdfplumber
- `DOWNLOAD_PDFS` (default: `false`): persist downloaded PDFs
- `DATA_DIR` (default: `data`): output path
- `LOGS_DIR` (default: `logs`): log directory

Example:

```bash
export MAX_DEPTH=3
export MAX_PAGES=200
export RATE_LIMIT_SECONDS=1.0
export EXTRACT_PDF_TEXT=true
```

## Run Instructions

From project root:

```bash
python -m app.main
```

## Output Artifacts

- `data/pages/*.json` -> one file per crawled page
- `data/aggregated.json` -> combined output across pages
- `data/metadata/crawl_metadata.json` -> crawl stats + runtime metadata
- `logs/crawler.log` -> crawler and scraper logs

Sample structured output is included at `data/sample_output.json`.

## Extraction Strategy

- Parse cleaned main content (`main`, `[role='main']`, IRCC content containers)
- Enumerate semantic headings (`h2`, `h3`)
- For each heading, gather sibling nodes until next heading
- Associate heading with related:
  - paragraphs/list items
  - `ul`/`ol` bullets
  - table rows/columns
- Classify each section by keyword scoring
- Detect canonical IRCC visa eligibility/supporting-document signals using dedicated mapping
- Normalize text and deduplicate list entries and URLs

## Extensibility Notes

- Replace keyword classifier in `app/scraper/classifier.py` with transformer/embedding models later
- Add language-specific pipelines for French content
- Add persistent queue backend (Redis/RabbitMQ) for very large crawl workloads
- Add state store (Postgres/S3) for distributed crawling
- Add incremental crawl delta support with ETag/Last-Modified

## Compliance and Operations

- Domain restriction to `canada.ca` and `ircc.canada.ca`
- Robots.txt aware crawling
- Retry/backoff for transient failures
- Structured logging for monitoring and auditing

## Known Operational Recommendations

- Use lower `RATE_LIMIT_SECONDS` only if policy allows
- Keep `OBEY_ROBOTS=true` in production
- Add integration tests against stable snapshots to detect IRCC page structure changes early
