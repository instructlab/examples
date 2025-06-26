# main.py
import argparse
from utils import get_supported_files, save_results, generate_summary
from analysis import convert_to_docling_document, analyze_docling_tables
from .log_utils import logger

def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for the Illuminator tool.

    Returns:
        argparse.Namespace containing:
            - file: Optional path to a single PDF.
            - dir: Optional path to a directory of PDFs.
            - output: Path to save results JSON file.
    """
    parser = argparse.ArgumentParser(description="Docling PDF Checker")
    parser.add_argument(
        "-f", "--file",
        help="Path to a PDF file or directory of PDFs",
        required=True
    )
    parser.add_argument(
        "-o", "--output",
        help="Optional path to save JSON results",
        default="results.json"
    )
    return parser.parse_args()

def main() -> None:
    """
    Main execution flow:
    - Parses arguments
    - Loads and analyzes PDFs or JSON files
    - Generates and saves results
    """
    args = parse_args()
    files = get_supported_files(args.file)
    if not files:
        logger.error("❌ No supported input files found to process.")
        return

    all_results = {}
    for path in files:
        logger.info(f"\n🔍 Converting and analyzing: {path}\n")
        try:
            # Use Docling to convert (PDF path)
            doc = convert_to_docling_document(path)
            result = analyze_docling_tables(doc)
            all_results[path] = result
        except Exception as e:
            logger.error(f"❌ Failed to process {path}: {e}")

    generate_summary(all_results)
    save_results(all_results, args.output)

if __name__ == "__main__":
    main()