from pathlib import Path
import hashlib
import json
import re

import pandas as pd
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

SOURCES_FILE = ROOT / "sources.csv"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
METADATA_DIR = ROOT / "data" / "metadata"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

METADATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_text(text: str) -> str:
    """
    Clean extracted text without aggressively
    deleting useful scholarship information.
    """

    if not text:
        return ""

    # Remove invisible characters
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = text.replace("\xa0", " ")

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    cleaned_lines = []

    for line in text.split("\n"):
        # Collapse spaces/tabs inside each line
        line = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        if not line:
            continue

        cleaned_lines.append(line)

    # Remove immediate duplicate lines
    final_lines = []
    previous = None

    for line in cleaned_lines:
        if line != previous:
            final_lines.append(line)

        previous = line

    return "\n".join(final_lines).strip()


# ---------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------

def node_text(node) -> str:
    """
    Extract readable text from a BeautifulSoup node.
    """

    text = node.get_text(
        separator="\n",
        strip=True,
    )

    return clean_text(text)


def extract_sharepoint_content(soup) -> str:
    """
    Microsoft SharePoint pages often store useful
    page content inside .ms-rtestate-field elements.

    We collect useful blocks instead of deleting
    the surrounding <form>.
    """

    blocks = []
    seen = set()

    candidates = soup.select(
        ".ms-rtestate-field"
    )

    for candidate in candidates:
        text = node_text(candidate)

        # Ignore tiny decorative blocks
        if len(text) < 40:
            continue

        # Avoid duplicate nested fields
        normalized = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if normalized in seen:
            continue

        seen.add(normalized)
        blocks.append(text)

    combined = "\n\n".join(blocks)

    return clean_text(combined)


def extract_generic_content(soup) -> str:
    """
    General extraction strategy for normal websites.
    """

    selectors = [
        "main",
        "article",
        '[role="main"]',
        "#main-content",
        "#content",
        ".main-content",
        ".page-content",
        ".content",
    ]

    candidates = []

    for selector in selectors:
        for node in soup.select(selector):
            text = node_text(node)

            if len(text) >= 100:
                candidates.append(text)

    if candidates:
        # Select the richest candidate
        return max(
            candidates,
            key=len,
        )

    if soup.body:
        return node_text(soup.body)

    return node_text(soup)


def parse_html(raw_data: bytes) -> str:
    """
    Parse HTML while preserving content inside
    forms. This is important for SharePoint pages.
    """

    soup = BeautifulSoup(
        raw_data,
        "lxml",
    )

    # -----------------------------------------------------
    # Remove content that never helps retrieval
    # IMPORTANT:
    # Do NOT remove "form".
    # SharePoint often places its real content inside forms.
    # -----------------------------------------------------

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
            "button",
        ]
    ):
        tag.decompose()

    # -----------------------------------------------------
    # SharePoint-specific extraction
    # -----------------------------------------------------

    sharepoint_content = (
        extract_sharepoint_content(soup)
    )

    # If SharePoint produced meaningful text,
    # prefer it over the whole page.
    if len(sharepoint_content) >= 200:
        return sharepoint_content

    # -----------------------------------------------------
    # Normal HTML extraction
    # -----------------------------------------------------

    return extract_generic_content(soup)


# ---------------------------------------------------------
# PDF parsing
# ---------------------------------------------------------

def parse_pdf(file_path: Path) -> str:
    """
    PDF support for future sources.
    Requires pypdf only when a PDF is encountered.
    """

    try:
        from pypdf import PdfReader

    except ImportError:
        raise RuntimeError(
            "A PDF source was found, but pypdf "
            "is not installed. Install it with: "
            "uv pip install pypdf"
        )

    reader = PdfReader(
        str(file_path)
    )

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""

        text = clean_text(text)

        if text:
            pages.append(text)

    return "\n\n".join(pages).strip()


# ---------------------------------------------------------
# Load source information
# ---------------------------------------------------------

def load_sources():
    if not SOURCES_FILE.exists():
        raise FileNotFoundError(
            f"sources.csv not found: "
            f"{SOURCES_FILE}"
        )

    dataframe = pd.read_csv(
        SOURCES_FILE
    )

    source_map = {}

    for _, row in dataframe.iterrows():
        source_id = str(
            row.get(
                "source_id",
                "",
            )
        ).strip()

        if not source_id:
            continue

        source_map[source_id] = {
            "source_id": source_id,
            "title": str(
                row.get(
                    "title",
                    "",
                )
            ),
            "provider": str(
                row.get(
                    "provider",
                    "",
                )
            ),
            "category": str(
                row.get(
                    "category",
                    "",
                )
            ),
            "url": str(
                row.get(
                    "url",
                    "",
                )
            ),
            "last_verified": str(
                row.get(
                    "last_verified",
                    "",
                )
            ),
        }

    return source_map


# ---------------------------------------------------------
# Process one raw source
# ---------------------------------------------------------

def process_source(
    file_path: Path,
    source_map: dict,
):
    source_id = file_path.stem

    print()
    print(
        f"Processing {source_id}"
    )

    raw_data = file_path.read_bytes()

    extension = (
        file_path.suffix.lower()
    )

    if extension in {
        ".html",
        ".htm",
    }:
        text = parse_html(
            raw_data
        )

        source_type = "html"

    elif extension == ".pdf":
        text = parse_pdf(
            file_path
        )

        source_type = "pdf"

    else:
        raise ValueError(
            f"Unsupported file type: "
            f"{extension}"
        )

    text = clean_text(text)

    # -----------------------------------------------------
    # Save processed text
    # -----------------------------------------------------

    output_file = (
        PROCESSED_DIR
        / f"{source_id}.txt"
    )

    output_file.write_text(
        text,
        encoding="utf-8",
    )

    # -----------------------------------------------------
    # Build metadata
    # -----------------------------------------------------

    source_info = source_map.get(
        source_id,
        {},
    )

    metadata = {
        "source_id": source_id,
        "title": source_info.get(
            "title",
            "",
        ),
        "provider": source_info.get(
            "provider",
            "",
        ),
        "category": source_info.get(
            "category",
            "",
        ),
        "url": source_info.get(
            "url",
            "",
        ),
        "last_verified": source_info.get(
            "last_verified",
            "",
        ),
        "raw_file": file_path.name,
        "processed_file": output_file.name,
        "source_type": source_type,
        "characters": len(text),
        "words": len(text.split()),
        "raw_sha256": sha256_bytes(
            raw_data
        ),
        "parser": (
            "beautifulsoup-lxml"
            if source_type == "html"
            else "pypdf"
        ),
    }

    metadata_file = (
        METADATA_DIR
        / f"{source_id}.json"
    )

    metadata_file.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"[OK] {source_id} -> "
        f"{output_file.name} "
        f"({len(text):,} characters, "
        f"{len(text.split()):,} words)"
    )

    if len(text) == 0:
        print(
            f"[WARNING] {source_id} "
            f"produced empty text."
        )

    elif len(text) < 500:
        print(
            f"[WARNING] {source_id} "
            f"produced very short text."
        )

    return {
        "source_id": source_id,
        "characters": len(text),
        "words": len(text.split()),
        "status": "success",
    }


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("Source Parsing")
    print("=" * 60)
    print()

    source_map = load_sources()

    raw_files = sorted(
        list(
            RAW_DIR.glob("*.html")
        )
        + list(
            RAW_DIR.glob("*.htm")
        )
        + list(
            RAW_DIR.glob("*.pdf")
        )
    )

    print(
        f"Found {len(raw_files)} "
        f"raw source files."
    )

    successful = 0
    failed = 0

    for file_path in raw_files:
        try:
            process_source(
                file_path,
                source_map,
            )

            successful += 1

        except Exception as error:
            failed += 1

            print(
                f"[FAILED] "
                f"{file_path.stem}: "
                f"{error}"
            )

    print()
    print("=" * 60)
    print("Parsing finished")
    print("=" * 60)
    print(
        f"Successful: {successful}"
    )
    print(
        f"Failed: {failed}"
    )


if __name__ == "__main__":
    main()