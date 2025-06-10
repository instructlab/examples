# Tests and Testing Utilities

Welcome to the `_tests` directory!

This section of the repository is dedicated to housing assets and utilities related to testing and quality assurance for the InstructLab examples. Its primary purpose is to support development and ensure the reliability and correctness of the examples and any shared code within the repository.

## Content Overview

* **`inference-mock/`**:
    * **Purpose:** This sub-directory contains a mock LLM inference server. It simulates the behavior of an OpenAI-compatible API endpoint, allowing for local, deterministic testing and development without requiring a live LLM service. This is particularly useful for:
        * **Local Development:** Quickly testing notebook logic that interacts with an LLM without needing to run a full LLM instance.
        * **Reproducible Testing:** Ensuring that tests relying on LLM responses are consistent and repeatable.
        * **CI/CD:** Enabling automated tests in Continuous Integration pipelines.
    * **Content Includes:**
        * `app.py`: The Flask application that serves the mock API.
        * `qna/`: Contains mock Q&A data or logic used by the mock server.
        * `requirements.txt`: Dependencies specific to running the mock server.

## How to Use

For instructions on how to set up and use specific testing utilities or mock servers, please refer to the `README.md` file within their respective sub-directories (e.g., `_tests/inference-mock/README.md`).