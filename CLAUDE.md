# CLAUDE.md

## Project Overview

This is a **Streamlit web application** template — a minimal starter project for building interactive web apps with Python and Streamlit. Licensed under Apache 2.0.

## Repository Structure

```
.
├── streamlit_app.py        # Main application entry point
├── requirements.txt        # Python dependencies
├── .devcontainer/          # VS Code Dev Container / Codespaces config
│   └── devcontainer.json
├── .github/
│   └── CODEOWNERS          # Owned by @streamlit/community-cloud
├── README.md
├── LICENSE                 # Apache 2.0
└── .gitignore
```

## Tech Stack

- **Language:** Python (3.11+ target, based on dev container config)
- **Framework:** [Streamlit](https://docs.streamlit.io/)
- **Default port:** 8501

## Getting Started

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

With dev container (CORS/XSRF disabled for local dev):
```bash
streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false
```

## Dependencies

Only dependency is `streamlit` (unpinned, uses latest).

## Key Files

- `streamlit_app.py` — Single entry point; all application logic goes here. Currently a minimal template with a title and welcome message.
- `requirements.txt` — Add Python packages here (one per line).
- `.devcontainer/devcontainer.json` — Configures VS Code Dev Containers / GitHub Codespaces with Python 3.11, auto-installs deps, and launches the app on port 8501.

## Development Conventions

- **No test framework, linter, or formatter is configured.** There are no CI/CD pipelines.
- **No build step required** — Streamlit apps run directly from Python source.
- When adding dependencies, add them to `requirements.txt`.
- The `.gitignore` excludes `.streamlit/secrets.toml` — use this for secrets management, never commit secrets.

## Common Commands

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements.txt` |
| Run app | `streamlit run streamlit_app.py` |

## Notes for AI Assistants

- This is a blank template project. The main app file (`streamlit_app.py`) is minimal and intended to be extended.
- There are no tests to run or linting checks to pass.
- When adding new features, follow Streamlit's declarative API patterns (use `st.*` functions).
- Keep `requirements.txt` updated when introducing new packages.
- Secrets should go in `.streamlit/secrets.toml` (git-ignored), accessed via `st.secrets`.
