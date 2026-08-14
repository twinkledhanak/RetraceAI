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

## Vector search (Atlas Automated Embedding)

`POST /search` gates the query through Gemini; when vector search is needed it runs a
`$vectorSearch` against your `Twinkle_DB.Upgrade_Sessions` collection using an
`autoEmbed` index. Atlas embeds the raw query text and the indexed fields
(`attempts.errorText`, `attempts.notes`) itself — no client-side embeddings.

### 1. Create the Atlas autoEmbed index

In the Atlas UI, create an Automated Embedding search index named `vector_index` on the
`Twinkle_DB.Upgrade_Sessions` collection that embeds the `attempts.errorText` and
`attempts.notes` fields. Atlas generates embeddings for existing and new documents
automatically.

### 2. Try it

```sh
curl -s -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "tailwindcss upgrade failed with oklch error"}' | jq .
```

Configurable via `RETRACE_MONGO_DB`, `RETRACE_MONGO_COLLECTION`,
`RETRACE_VECTOR_INDEX_NAME`, `RETRACE_VECTOR_PATH` (the indexed field, default
`attempts.errorText`).

## Writing upgrade sessions to Atlas

`POST /sessions` inserts a new upgrade session into `Twinkle_DB.Upgrade_Sessions`. The
`autoEmbed` index embeds it automatically — no manual embedding step.

```sh
curl -s -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "s2",
    "appVersion": {"from": "v2", "to": "v3"},
    "status": "resolved",
    "attempts": [
      {
        "library": "vite",
        "action": "upgrade",
        "fromVersion": "4.0.0",
        "toVersion": "5.0.0",
        "succeeded": true,
        "notes": "swapped rollup config to rolldown"
      }
    ],
    "coupledWith": ["vite", "vitest"]
  }' | jq .
```

Returns the created document (with its `_id`). `timestamp` defaults to now if omitted.

## Updating a session (append an attempt)

The write layer lives in `src/retraceai/memory.py` — call `add_attempt_to_session(session_id, attempt)`
from anywhere in the code (it logs `Step 2: Invoking Atlas to modify document and add new information
to memory`). The same function powers `POST /sessions/{sessionId}/attempts` and the convenience
script below.

Append an attempt without curl:

```sh
python scripts/remember.py s2 \
  --library vite --action downgrade --to-version 4.0.0 \
  --succeeded false --error-text "rolldown missing plugin"
```

Or via the API:

```sh
curl -s -X POST http://127.0.0.1:8000/sessions/s2/attempts \
  -H "Content-Type: application/json" \
  -d '{
    "library": "vite",
    "action": "downgrade",
    "fromVersion": "5.0.0",
    "toVersion": "4.0.0",
    "succeeded": false,
    "errorText": "rolldown missing plugin"
  }' | jq .
```

The function raises `KeyError` if no session has that `sessionId` (API: `404`) and `RuntimeError`
on Atlas failures (API: `503`). The `autoEmbed` index re-embeds automatically when
`attempts.errorText`/`notes` change.
