#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/server"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install -e ".[test]"
mkdir -p ../../data
python -m quipu_server.seed ../../fixtures/ingest/team-sample.json --database ../../data/quipu.sqlite3
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 127.0.0.1 --port 8000 --reload
