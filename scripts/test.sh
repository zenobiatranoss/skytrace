#!/usr/bin/env bash
# run whatever tests exist, backend and frontend
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== backend =="
(cd "$ROOT/backend" && "$ROOT/.venv/bin/python" -m pytest -q)

echo "== frontend =="
if [ -d "$ROOT/frontend/node_modules" ]; then
  (cd "$ROOT/frontend" && npm run test)
else
  echo "skipped, node_modules missing"
fi
