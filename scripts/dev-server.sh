#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/server"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install -e ".[test]"
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 0.0.0.0 --port 8000 --reload
