# Codex Project Doc

This document is discovered automatically by **OpenAI Codex CLI** when it runs inside this repository.
It provides high‑level context and guard‑rails so the agent can test, improve, and deploy the Samsara
Fleet Manager safely.

## Purpose
Manage driver records in the Samsara Fleet platform (create, update, deactivate) and publish a daily
report via e‑mail. The program is triggered by Windows Task Scheduler or can be executed manually.

## How to run locally

```bash
# Install deps
python -m pip install -r requirements.txt -r requirements-dev.txt

# Make sure you have an .env file (see .env.example)
python main.py --dry-run
```

## Quality gates

* **Unit tests:** `pytest -q`
* **Linter:** `ruff check .`
* **Formatting (optional):** `ruff format .`

A pull‑request is ready to merge when all the above commands succeed.

## Coding guidelines

1. Target **Python 3.11+**.
2. Never commit secrets – they must be loaded from environment variables or `.env`.
3. Follow PEP 8 style (enforced by Ruff).
4. Keep new dependencies minimal and pin them in `requirements*.txt`.

---
_Last updated: 2025-07-29_
