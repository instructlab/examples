# main.py
import argparse
from utils import get_pdf_files, save_results, generate_summary
from analysis import analyze_pdf_with_docling
from log_utils import logger

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
    - Loads and analyzes PDFs
    - Generates and saves results
    """
    args = parse_args()
    pdfs = get_pdf_files(args.file)
    if not pdfs:
        logger.error("❌ No PDFs found to process.")
        return

    all_results = {}
    for path in pdfs:
        logger.info(f"\n🔍 Converting and analyzing: {path}\n")
        try:
            result = analyze_pdf_with_docling(path)
            all_results[path] = result
        except Exception as e:
            logger.error(f"❌ Failed to process {path}: {e}")

    generate_summary(all_results)
    save_results(all_results, args.output)

if __name__ == "__main__":
    main()
