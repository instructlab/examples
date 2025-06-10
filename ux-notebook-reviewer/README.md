 ## Try out on the cloud

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/instructlab/examples/blob/ux-notebook-reviewer/ux-notebook-reviewer/ux_notebook_reviewer.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/instructlab/examples/ux-notebook-reviewer?urlpath=lab/tree/ux-notebook-reviewer/ux_notebook_reviewer.ipynb)

# UX Notebook Reviewer

An interactive Jupyter Notebook tool designed to **automate User Experience (UX) reviews** of other notebooks against a set of best-practice guidelines, leveraging your local Large Language Model (LLM) via Ollama/OpenAI.

## Why Use This Tool?

### 1. Consistent & Objective Feedback
Manual UX reviews are time-consuming and prone to inconsistencies. This tool enforces a uniform checklist, ensuring no critical element—like a missing header or setup instruction—is overlooked. By codifying UX guidelines into a strict Markdown table and integrating an LLM, it provides high-level compliance scores and actionable suggestions, minimizing bias and fatigue.

### 2. Accelerated Iteration
Perform a comprehensive UX audit in under a minute. The tool provides immediate, data-driven feedback, allowing for rapid issue resolution and re-verification, significantly accelerating your development cycles.

### 3. Streamlined Onboarding & Collaboration
New team members can instantly grasp and apply your established UX standards. This tool facilitates early quality checks, enabling automated 'UX check' badges for pull requests before human review, fostering a culture of consistency.

## Key Features

* **Interactive File Upload:** Seamlessly drag-and-drop any `.ipynb` file for immediate inspection and analysis.
* **Live Progress Indicators:** A visual spinner and elapsed time display provide real-time feedback on review progress.
* **Structured Output:** Generates a concise, GitHub-flavored Markdown table with clear status icons (✅, 🔹, ❌, –) and tailored suggestions for each guideline.
* **LLM-Powered Analysis:** Utilizes an LLM to perform a deep-dive evaluation and populate the review table.
* **Clean Output:** Guarantees "only the table" is returned, ensuring output can be directly embedded in documentation or pull request descriptions without extraneous prose.

## Installation

To set up and run the UX Notebook Reviewer:

1.  **Clone this repository:**
    ```bash
    git clone [https://github.com/your-org/ux-notebook-reviewer.git](https://github.com/your-org/ux-notebook-reviewer.git)
    cd ux-notebook-reviewer
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install nbformat openai ipywidgets
    jupyter nbextension enable --py widgetsnbextension
    ```

3.  **Run Ollama (or point to your OpenAI endpoint):**
    ```bash
    ollama serve
    ```

4.  **Open the Reviewer Notebook:**
    ```bash
    jupyter lab notebooks/ux_notebook_reviewer.ipynb
    ```

## Usage Guide

1.  **Upload a Notebook:**
    * Execute the first cell in the notebook.
    * Drag your `.ipynb` file into the displayed `FileUpload` widget.

2.  **Review UX:**
    * Run the "Automated UX Review" cell.
    * Observe the live "🧠 Evaluating…" spinner with its elapsed time.
    * A concise legend and a GitHub-flavored Markdown table will display the review status with icons and suggestions.

3.  **Iterate:**
    * Address any flagged issues (red ❌ or blue 🔹 items) in your target notebook.
    * Re-run the "Automated UX Review" cell for instant confirmation of improvements.

## Configuration

**Model Selection:**
* By default, the reviewer uses `llama3.1:8b-instruct-fp16`.
* To change the model, edit the `model=` argument directly within the review cell's code.