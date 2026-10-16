# Development

## Backend

```bash
cd backend
python3 -m venv ../.venv
../.venv/bin/pip install -r requirements.txt
../.venv/bin/uvicorn app.main:app --reload
```

Or just `./scripts/dev.sh` from the repo root to run both halves.

The API is under `/api`. Interactive docs at `/docs`.

### Configuration

All settings live in `app/core/config.py` and read from `.env`. See
`.env.example` for the full list.

### Tests

```bash
cd backend
../.venv/bin/python -m pytest -q
```

Tests use a separate sqlite file and never call the network. The lifespan
(and therefore the live poller) is skipped by not using the TestClient as
a context manager.

### Database

SQLite, created on startup from the SQLAlchemy models. Delete
`skytrace.db` to start clean.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/ws` to the backend on `:8000` (see
`vite.config.ts`).

### Tests

```bash
cd frontend
npm run test        # vitest, single run
npm run test:watch  # watch mode
```

Vitest runs in jsdom (see the `test` block in `vite.config.ts`). Unit
tests cover the coordinate/formatter helpers and the websocket decoder;
component tests use testing-library.

## Conventions

- Code and comments in English.
- Comments only where they earn their place - not on obvious lines.
- Missing data stays `null`; the UI renders it as unavailable.
