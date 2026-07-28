# Contributing

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Checks

Run the same checks as CI before opening a pull request:

```bash
ruff format --check .
ruff check .
mypy src/search1api_langchain
pytest
python -m build
```

Tests must not call the production Search1API service or include API keys.
