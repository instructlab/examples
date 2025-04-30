# Notebook UX Review Template
Use this template to review notebooks using the UX guidelines.

## Instructions
- Open the notebook you're reviewing in another tab or split window.
- Use the table below to summarize UX alignment.
- Mark each guideline as:
  - ✅ Meets expectations
  - 🔹 Could be improved
  - ❌ Missing
  - ➖ Not applicable
- Add a short note in the *Suggestion* column for action items.
- Submit it as a comment in a PR

## UX Structure Review Summary

✅ = (Meets expectations)  
🔹 = (Could be improved)  
❌ = (Missing)  
➖ = Not applicable

| Guideline | Status | Suggestion |
|-----------|--------|------------|
| Clear Header | ✅🔹❌➖ | Clear, succinct title (<15 words) of notebook's purpose |
| Goal/Objective Present | ✅🔹❌➖ | Brief summary (1–2 lines) of what the notebook does and why |
| Setup & Pre-Requisites | ✅🔹❌➖ | Includes installation steps, required files, and environment assumptions |
| Section Headers/Markdown | ✅🔹❌➖ | Each code cell/section is preceded by a markdown block explaining its purpose |
| Handle Errors or Outputs | ✅🔹❌➖ | Highlights expected outputs or common errors (e.g. YAML structure, missing files, etc...) |
| Hardcoding Avoided | ✅🔹❌➖ | Uses variables or config for file paths instead of hardcoded strings |
| Concise Cells | ✅🔹❌➖ | Breaks logic into manageable chunks; avoids long, dense blocks |
| Code Commenting | ✅🔹❌➖ | Inline comments clarify non-obvious logic or structure within code cells |
| End Wrap-Up & Handoff | ✅🔹❌➖ | Notebook ends with a summary and/or next step guidance |

---
### Reviewer Notes (Optional)
Leave additional comments or clarifications here.