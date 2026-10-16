#!/usr/bin/env bash
# run backend and frontend together for local work
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$ROOT/.venv" ]; then
  echo "creating venv..."
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"
fi

if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "installing frontend deps..."
  (cd "$ROOT/frontend" && npm install)
fi

echo "starting backend on :8000"
(cd "$ROOT/backend" && "$ROOT/.venv/bin/uvicorn" app.main:app --reload --port 8000) &
BACKEND_PID=$!

echo "starting frontend on :5173"
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
