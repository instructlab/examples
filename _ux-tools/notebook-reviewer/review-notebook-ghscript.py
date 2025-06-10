#!/usr/bin/env python3
"""
scripts/review_notebooks.py

Scan notebooks in the repo, run a UX review via an LLM, and output Markdown to stdout or file.

Usage:
    python scripts/review_notebooks.py --path notebooks/  # or .
"""
import os
import sys
import argparse
import nbformat
import time
from openai import OpenAI  # or import openai if using openai-python; adjust accordingly
# If you use openai-python: `import openai` and set openai.api_key = ...
# Here we assume OpenAI(base_url=..., api_key=...) or default openai.api_key from env.

def extract_notebook_text(nb):
    return "\n\n".join(cell.source for cell in nb.cells)

def review_notebook_text(notebook_text: str, client, model: str = "gpt-4"):
    """
    Send a single-prompt to the LLM to review the notebook_text.
    Returns the raw Markdown table output (string).
    """
    # Build legend & table skeleton, similar to your notebook code
    legend_md = """**Legend (each icon is a %-based score):**  
✅ 90–100% compliance (excellent)  
🔹 60–89% compliance (good but needs a little work)  
❌ 0–59% compliance or completely missing (major issue)  
– not applicable  
"""
    table_template = """
| Guideline              | Status | Suggestion                                        |
|------------------------|--------|:--------------------------------------------------|
| Clear Header           |        |                                                   |
| Goal/Objective Present |        |                                                   |
| Setup & Pre-Requisites |        |                                                   |
| Markdown Usage         |        |                                                   |
| Avoid Hardcoding       |        |                                                   |
| Inline Code Comments   |        |                                                   |
| Next Steps & Conclusion|        |                                                   |
"""
    prompt = f"""
Here is a Jupyter notebook for review (full content follows):

{notebook_text}

{legend_md}

Return *only* a GitHub-flavored Markdown table with exactly these columns and rows filled in:

{table_template}

Fill each row’s Status (using ✅, 🔹, ❌, or –) and Suggestion. Use ❌ if the guideline is completely missing.
"""
    # Call the LLM
    # If using openai-python:
    # response = openai.ChatCompletion.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": "You are a helpful UX reviewer of technical Jupyter Notebooks."},
    #         {"role": "user",   "content": prompt},
    #     ],
    #     temperature=0.3,
    # )
    # raw_md = response.choices[0].message.content
    # If using OpenAI(...) client pattern:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful UX reviewer of technical Jupyter Notebooks."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
    )
    raw_md = response.choices[0].message.content
    return raw_md

def main():
    parser = argparse.ArgumentParser(description="Review Jupyter notebooks in a path via LLM")
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Path to search for .ipynb files (recursively)."
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Optional: write combined Markdown to this file instead of stdout."
    )
    parser.add_argument(
        "--model", "-m",
        default=os.getenv("LLM_MODEL", "gpt-4"),
        help="LLM model name (e.g. gpt-4, gpt-3.5-turbo)."
    )
    args = parser.parse_args()

    # Initialize LLM client:
    # Option A: using openai-python:
    # import openai
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    # client = openai
    # Option B: using OpenAI(...) pattern:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL", None), api_key=api_key)
    model = args.model

    # Find notebooks
    nb_paths = []
    for root, dirs, files in os.walk(args.path):
        # optionally skip .ipynb_checkpoints
        dirs[:] = [d for d in dirs if d != ".ipynb_checkpoints"]
        for fname in files:
            if fname.endswith(".ipynb"):
                nb_paths.append(os.path.join(root, fname))
    if not nb_paths:
        print("No .ipynb files found under", args.path)
        sys.exit(0)

    results = []
    for nb_path in nb_paths:
        print(f"Reviewing {nb_path} ...", file=sys.stderr)
        try:
            nb = nbformat.read(nb_path, as_version=4)
        except Exception as e:
            print(f"  ❌ Failed to read {nb_path}: {e}", file=sys.stderr)
            continue
        notebook_text = extract_notebook_text(nb)
        # Optionally truncate if huge, or only pass first N cells
        raw_md = review_notebook_text(notebook_text, client, model=model)
        # Prepend a header per notebook
        header = f"## Review of `{nb_path}`\n\n"
        results.append(header + raw_md + "\n\n")
        # Sleep between calls if rate-limited
        time.sleep(1)

    combined = "\n".join(results)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(combined)
        print(f"Wrote review to {args.output}", file=sys.stderr)
    else:
        print(combined)

if __name__ == "__main__":
    main()
