from pathlib import Path
import time

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

SOURCES_FILE = ROOT / "sources.csv"
RAW_DIR = ROOT / "data" / "raw"
METADATA_DIR = ROOT / "data" / "metadata"

RAW_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = METADATA_DIR / "fetch_report.csv"


# ---------------------------------------------------------
# HTTP session
# ---------------------------------------------------------

session = requests.Session()

retries = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504,
    ],
    allowed_methods=["GET"],
)

adapter = HTTPAdapter(max_retries=retries)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/130.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,"
            "application/pdf;q=0.8,*/*;q=0.7"
        ),
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Connection": "keep-alive",
    }
)


# ---------------------------------------------------------
# Fetch one source
# ---------------------------------------------------------

def fetch_source(source):
    source_id = str(source["source_id"]).strip()
    title = str(source["title"]).strip()
    url = str(source["url"]).strip()

    print(f"Processing {source_id}")
    print(f"Title: {title}")
    print(f"URL: {url}")

    try:
        response = session.get(
            url,
            timeout=30,
            allow_redirects=True,
        )

        response.raise_for_status()

        content_type = (
            response.headers
            .get("Content-Type", "")
            .lower()
        )

        # Detect PDF
        if (
            "application/pdf" in content_type
            or response.content[:4] == b"%PDF"
        ):
            extension = ".pdf"

        else:
            extension = ".html"

        output_file = RAW_DIR / f"{source_id}{extension}"

        output_file.write_bytes(response.content)

        size = len(response.content)

        print(
            f"[OK] {source_id} -> "
            f"{output_file.name} "
            f"({size:,} bytes)"
        )

        return {
            "source_id": source_id,
            "title": title,
            "url": url,
            "status": "success",
            "http_status": response.status_code,
            "content_type": content_type,
            "file": output_file.name,
            "bytes": size,
            "error": "",
        }

    except requests.RequestException as error:
        print(
            f"[FAILED] {source_id}: "
            f"{error}"
        )

        return {
            "source_id": source_id,
            "title": title,
            "url": url,
            "status": "failed",
            "http_status": "",
            "content_type": "",
            "file": "",
            "bytes": 0,
            "error": str(error),
        }

    except Exception as error:
        print(
            f"[FAILED] {source_id}: "
            f"{error}"
        )

        return {
            "source_id": source_id,
            "title": title,
            "url": url,
            "status": "failed",
            "http_status": "",
            "content_type": "",
            "file": "",
            "bytes": 0,
            "error": str(error),
        }


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    if not SOURCES_FILE.exists():
        print(
            f"[ERROR] sources.csv not found: "
            f"{SOURCES_FILE}"
        )
        return

    sources = pd.read_csv(SOURCES_FILE)

    required_columns = {
        "source_id",
        "title",
        "url",
    }

    missing_columns = (
        required_columns
        - set(sources.columns)
    )

    if missing_columns:
        print(
            "[ERROR] Missing columns in sources.csv:"
        )

        for column in sorted(missing_columns):
            print(f" - {column}")

        return

    # Remove rows without URL
    sources = sources.dropna(
        subset=[
            "source_id",
            "title",
            "url",
        ]
    )

    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Source Ingestion")
    print("=" * 60)
    print()
    print(
        f"Running ingestion on "
        f"{len(sources)} sources..."
    )
    print()

    results = []

    for _, source in sources.iterrows():
        result = fetch_source(source)

        results.append(result)

        print("-" * 60)

        # Small polite delay between websites
        time.sleep(0.5)

    report = pd.DataFrame(results)

    report.to_csv(
        REPORT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    successful = (
        report["status"] == "success"
    ).sum()

    failed = (
        report["status"] == "failed"
    ).sum()

    html_files = (
        report["file"]
        .fillna("")
        .str.endswith(".html")
    ).sum()

    pdf_files = (
        report["file"]
        .fillna("")
        .str.endswith(".pdf")
    ).sum()

    print()
    print("=" * 60)
    print("Ingestion finished")
    print("=" * 60)
    print(f"Total sources: {len(report)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"HTML files: {html_files}")
    print(f"PDF files: {pdf_files}")
    print()
    print(
        f"Report saved to: "
        f"{REPORT_FILE}"
    )


if __name__ == "__main__":
    main()