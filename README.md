# SermonForge AI ⛪

> **A Premium, Decoupled Sermon Preparation Studio Integrated on Gloo Native RAG**
> 
> *The pastor brings the anointing and the personalized message — SermonForge AI handles the structural groundwork and scriptural research so you can focus on spiritual depth.*

---

SermonForge AI has been reorganized into a **decoupled folder architecture** with clear separation between concerns:

- **`backend/`**: Consolidates all FastAPI server code, Gloo vector database RAG indexes, prompt routing systems, markdown parser logic, and unit testing suites.
- **`frontend/`**: Created and kept **empty** as of now, reserved for future frontend implementations.

---

## 📂 Project Structure

```
Sermon_prep/
├── backend/
│   ├── main.py                  # FastAPI Backend API Server
│   ├── app_logger.py            # UUID Traced Logging (Console & Loki)
│   ├── bible_indexer.py         # Scriptural CSV Vector Uploader
│   ├── test_sermon_api.py       # Comprehensive Unit Testing Suite
│   └── pyproject.toml           # Poetry Configuration
├── frontend/
│   └── .gitkeep                 # Folder placeholder (kept empty)
└── README.md                    # Main Project Directory Guidelines
```

---

## 🚀 Backend Launch & Setup Guide

Open your command-line terminal, navigate to the **`backend`** directory, and run the following:

### Step 1: Install Dependencies
```bash
cd backend
poetry install
```
*(If you are not using Poetry, run `pip install fastapi uvicorn requests python-dotenv`)*

### Step 2: Start the FastAPI Backend Server
Start the Uvicorn web server on port `8000`:
```bash
poetry run uvicorn main:app --reload --port 8000
```
- The backend API server is now running on `http://127.0.0.1:8000`.
- The main sermon preparation generation RAG endpoint is exposed at: `POST http://127.0.0.1:8000/sermonai-api/ark-ai`

### Step 3: Run the Test Suite
Confirm the endpoint, Pydantic inputs, and markdown parsers are fully functional by running the test suite:
```bash
poetry run python test_sermon_api.py
```
*(You can also run tests without Poetry by executing `..\venv\Scripts\python test_sermon_api.py` from the `backend/` folder)*
