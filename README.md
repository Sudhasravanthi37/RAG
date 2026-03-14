# RAG — Retrieval-Augmented Generation Demo

Lightweight RAG system combining an Angular frontend with a FastAPI backend. The backend handles ingestion, chunking, embeddings, and a vector store (FAISS); the frontend provides authentication and an interactive chat/UI to ask questions over uploaded documents and static knowledge bases.

## Key Features
- FastAPI backend with modular `app` package (auth, ingestion, rag, llm, db).
- Angular frontend (SPA) for login, chat, file upload and profile management.
- Support for building static vector DBs (medical, resume) and per-upload vector DBs.
- Multiple modes: Q&A, translator, resume analysis, legal/medical helpers, etc.

## Repository Layout
- `backend/` — Python FastAPI app and ingestion pipeline.
- `frontend/` — Angular application source.
- `data/` — runtime artifacts: `uploads/`, `vector_dbs/`, `static/`, `profile_pics/`.

## Prerequisites
- Python 3.10+ for the backend
- Node.js 18+ and npm for the frontend
- (Optional) GPU or sufficiently powerful CPU for embedding generation

## Backend — Quick Start
1. Open a terminal and create a venv:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2. Create and edit environment variables (copy from example if present):

```powershell
copy .env.example .env
# Edit .env to set keys like GROQ_API_KEY, DATABASE_URL, JWT_SECRET_KEY
```

3. (Optional) Build static vector DBs:

```powershell
python -m app.static_dbs.static_db_builder
```

4. Run the backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Frontend — Quick Start
1. Install dependencies and run dev server:

```bash
cd frontend
npm install
npm start
```

2. Open `http://localhost:4200` in your browser.

## Data & Artifacts
- Uploaded files are stored under `data/uploads/` and per-upload vector DBs under `data/vector_dbs/`.
- Static DBs live under `data/static/vector_dbs/` (medical, resume).
- Large binary artifacts (Faiss index files) should be ignored in git — see `.gitignore`.

## Environment Variables (example keys)
- `GROQ_API_KEY` — Groq or embeddings service key
- `DATABASE_URL` — e.g. `sqlite:///./data/app.db`
- `JWT_SECRET_KEY` — secret for signing tokens
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` — email for OTPs
- `FRONTEND_VERIFY_URL` — frontend base URL for verification links

## Useful Backend Endpoints
- `POST /auth/login` — login
- `POST /auth/signup` — signup
- `POST /upload` — upload files for ingestion
- `GET /chats` — list chats
- `POST /chat` — send chat message / query

## Development Tips
- Inspect `backend/app/config.py` for env variable names and defaults.
- Use the provided `static_dbs` scripts to pre-build domain-specific indexes.
- Keep `data/` and `node_modules/` out of git (already in `.gitignore`).

## Contributing
- Open an issue or submit a PR. Keep changes small and provide tests where practical.

## License
This repository does not include a license file. Add one (e.g., MIT) if you plan to publish.

