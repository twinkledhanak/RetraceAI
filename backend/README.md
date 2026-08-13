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

MongoDB Atlas connection:

```sh
export RETRACE_MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
```

## Gemini (Vertex AI)

The model, GCP project, and location are configurable via `RETRACE_GEMINI_MODEL`,
`RETRACE_GCP_PROJECT`, and `RETRACE_GCP_LOCATION` (see `src/retraceai/config.py`).

Authenticate with a service account JSON or ADC:

```sh
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
# or
gcloud auth application-default login
```

Run the live Gemini test (skipped automatically when no credentials are found):

```sh
pytest tests/test_gemini.py -s
```
