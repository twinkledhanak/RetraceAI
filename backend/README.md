# RetraceAI Backend

FastAPI backend for RetraceAI.

## Setup

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```sh
uvicorn retraceai.main:app --reload
```

Interactive docs at http://127.0.0.1:8000/docs

## Test & lint

```sh
pytest
ruff check src tests
```

## Config

Settings are read from environment variables with the `RETRACE_` prefix or a `.env` file
(e.g. `RETRACE_PORT=8000`, `RETRACE_DEBUG=true`). See `src/retraceai/config.py`.
