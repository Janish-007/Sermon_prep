# SermonForge AI ⛪

> A decoupled sermon preparation studio with a Streamlit frontend and FastAPI backend powered by Gloo Native RAG.

## Project Structure

```
Sermon_prep/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI backend API server
│   ├── app_logger.py            # UUID-traced logging
│   ├── bible_indexer.py         # Scriptural CSV vector uploader
│   ├── requirements.txt         # pip dependency list
│   └── test_sermon_api.py       # backend test suite
├── data/
│   └── sermon_history.json      # local Streamlit sermon history
├── frontend/
│   └── app.py                   # Streamlit sermon prep studio
├── Dockerfile                   # backend container image
├── pyproject.toml               # Poetry project configuration
├── poetry.lock                  # Poetry lockfile
└── README.md
```

## Backend

Install dependencies from the project root:

```bash
poetry install
```

Start the FastAPI server:

```bash
poetry run uvicorn backend.main:app --reload --port 8000
```

The sermon generation endpoint is:

```text
POST http://127.0.0.1:8000/sermonai-api/ark-ai
```

Supported sermon payload fields include `topic`, `scripture`, `style`, `duration`, `audience`, `denomination`, and `lang`. The `denomination` field defaults to `General Christian` and can be used to shape theological emphasis and pastoral application.

## Frontend

Start the Streamlit app from the project root:

```bash
poetry run streamlit run frontend/app.py
```

Saved sermon history is stored in `data/sermon_history.json`.

## Tests

Run the backend test suite:

```bash
cd backend
poetry run python test_sermon_api.py
```

## Environment

Create `backend/.env` with the required Gloo credentials:

```text
GLOO_CLIENT_ID=...
GLOO_CLIENT_SECRET=...
GLOO_PUBLISHER_ID=...
GLOO_TENANT_NAME=...
GLOO_COLLECTION=...
```
