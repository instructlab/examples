from docling.document_converter import DocumentConverter
from docling.datamodel.document import DoclingDocument
from typing import List, Tuple, Dict, Any, Union, Set
from .log_utils import logger
import os

def cell_is_merged(cell) -> bool:
    """
    Determines whether a table cell is merged based on its row or column span.

    Args:
        cell: A table cell object from the Docling document.

    Returns:
        True if the cell spans multiple rows or columns; False otherwise.
    """
    return (
        cell.col_span > 1 or
        cell.row_span > 1
    )

def summarize_tables(doc) -> Tuple[int, List[int]]:
    """
    Summarizes tables and extracts the page numbers they appear on.

    Args:
        doc: A DoclingDocument object.

    Returns:
        A tuple containing:
            - The number of tables found.
            - A list of page numbers on which the tables are located.
    """
    tables = doc.tables
    num_tables = len(tables)
    pages = []

    for table in tables:
        for prov in table.prov:
            pages.append(prov.page_no)

    return num_tables, pages

def convert_to_docling_document(file_path: str) -> DoclingDocument:
    """
    Converts a PDF using Docling and saves a Markdown version of the document.

    Args:
        file_path: Path to the input PDF file.

    Returns:
        The converted Docling Document object.
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document

    # Save Markdown output
    markdown_text = doc.export_to_markdown()
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    md_output_path = f"{base_name}.md"
    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    logger.info(f"📝 Markdown saved to {md_output_path}")
    return doc

def analyze_docling_tables(doc_input: DoclingDocument) -> Dict[str, Union[int, List[dict], List[int], str]]:
    """
    Analyzes a Docling document (object or path to PDF/JSON file) for merged table cells.
    """

    table_count, table_pages_list = summarize_tables(doc_input)
    total_pages = len(set(table_pages_list)) or "Unknown"

    issues = {
        "merged_table_cells": [],
        "table_count": table_count,
        "merged_cell_pages": set(),
        "page_count": total_pages
    }

    for i, table_item in enumerate(doc_input.tables):
        try:
            page_number = table_pages_list[i]
        except IndexError:
            page_number = "Unknown page"
        table_data = table_item.data

        for row_idx, row in enumerate(table_data.grid):
            for col_idx, cell in enumerate(row):
                if cell_is_merged(cell):
                    issues["merged_table_cells"].append({
                        "page": page_number,
                        "row": row_idx,
                        "column": col_idx,
                        "colspan": cell.col_span,
                        "rowspan": cell.row_span,
                        "text": cell.text or "[empty]"
                    })

                    if isinstance(page_number, int):
                        issues["merged_cell_pages"].add(page_number)

    issues["merged_cell_pages"] = sorted(issues["merged_cell_pages"])
    return issues