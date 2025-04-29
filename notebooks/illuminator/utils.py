# utils.py
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from log_utils import logger

MAX_PREVIEW_LENGTH = 30  # Max characters shown from cell text in summary

def get_pdf_files(path: str) -> List[str]:
    """
    Returns a list of PDF file paths from a given file or directory.

    Args:
        path: Path to a single .pdf file or directory containing .pdf files.

    Returns:
        List of .pdf file paths.
    """
    if os.path.isfile(path) and path.endswith(".pdf"):
        return [path]
    elif os.path.isdir(path):
        return [
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.endswith(".pdf")
        ]
    return []

def save_results(results, output_file: str) -> None:
    """
    Saves the results dictionary to a JSON file.

    Args:
        results: The analysis results to save.
        output_file: Desired filename. If it already exists or is the default 'results.json',
                     a UTC timestamp will be appended to avoid overwriting.
    """
    base, ext = os.path.splitext(output_file)
    original_output = output_file

    # If default filename or existing file, add a UTC timestamp
    if output_file == "results.json" or os.path.exists(output_file):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = f"{base}_{timestamp}_UTC{ext}"
        if original_output != output_file:
            logger.info(f"ℹ️  Output file '{original_output}' exists or is default. Saving as '{output_file}' instead.")

    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
    logger.info(f"📁 Results saved to {output_file}")

def generate_summary(results) -> None:
    """
    Prints a human-readable summary of merged table cell issues per file.

    Args:
        results: Dictionary containing analysis results for each PDF.
    """
    logger.info("📊 Summary Report")
    logger.info("=" * 50)
    for file, data in results.items():
        logger.info(f"\n📂 File: {file}")

        total_tables = data.get("table_count", 0)
        merged_cells = data.get("merged_table_cells", [])
        tables_with_merged_cells = len(set(cell["page"] for cell in merged_cells))

        if total_tables == 0:
            logger.info("ℹ️  No tables detected in this document.")
            continue

        logger.info(f"📋 Found {total_tables} table(s); {tables_with_merged_cells} table(s) have merged cells.")

        if not data.get("merged_cell_pages"):
            logger.info("✅ Tables detected, but no merged cells found.")
            continue

        pages = format_pages(data["merged_cell_pages"])
        logger.info(f"⚠️ Merged Table Cells Detected on Pages: {pages}")

        for cell in merged_cells:
            page = cell.get("page")
            text = cell.get("text", "").strip()
            if len(text) > MAX_PREVIEW_LENGTH:
                text = text[:MAX_PREVIEW_LENGTH] + "..."
            logger.info(f"   - Page {page}: \"{text}\" (row={cell['row']}, column={cell['column']})")

def format_pages(pages) -> str:
    """
    Compresses a list of individual page numbers into a readable string with ranges.

    Useful for displaying page numbers like "1, 2, 3, 5, 6, 7" as "1-3, 5-7".

    Args:
        pages: A list of page numbers (integers), typically where merged table cells were detected.

    Returns:
        A condensed string representation of the page list (e.g., "2-4, 6, 8-10").
    """
    if not pages:
        return ""
    pages = sorted(set(pages))
    ranges = []
    start = pages[0]
    for i in range(1, len(pages)):
        if pages[i] != pages[i - 1] + 1:
            if start == pages[i - 1]:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{pages[i - 1]}")
            start = pages[i]
    if start == pages[-1]:
        ranges.append(f"{start}")
    else:
        ranges.append(f"{start}-{pages[-1]}")
    return ", ".join(ranges)
