# Examples 

The `examples` repo is a place where the maintainers of the project can collect notebooks for the benefit of the community.

This repository contains [Jupyter notebooks](https://jupyter.org/) and other examples that illustrate parts of or an entire model customization pipeline.

## Repository Structure

Notebooks either live in the `combined-stages` or `use-cases` directories.

```bash
examples
|
|- notebooks
    |
    |- combined-stages
    |   |- training-with-eval
    |       |- requirements.txt
    |       |- training-with-eval.ipynb
    |- use-cases
    |   |- policy-documents
    |   |   |- requirements.txt
    |   |   |- legislative-act.ipynb
    |   |- instruction-manuals
    |   |   |- requirements.txt
    |   |   |- how-to-build-a-house.ipynb
```

### Notebooks for Combined InstructLab stages

Notebooks in the `combined-stages` directory go through parts of or an entire model customization workflow that users might want to reference or use.
Some examples of combined stages are a notebook that runs through training then evaluation or a notebook that goes from document pre-processing to synthetic data generation.

### Notebooks for End-to-End (e2e) use cases

Notebooks in the `use-cases` directory reflect real world use cases from start to finish.
