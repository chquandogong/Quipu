from pathlib import Path
import argparse
import json
import sqlite3

from quipu_server.contracts import ObservationBatchIn
from quipu_server.db import connect, initialize
from quipu_server.repository import ingest_batch
from quipu_server.settings import Settings


def load_fixture(path: Path) -> list[ObservationBatchIn]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [ObservationBatchIn.model_validate(item) for item in raw]


def seed_batches(conn: sqlite3.Connection, batches: list[ObservationBatchIn]) -> int:
    inserted = 0
    for batch in batches:
        result = ingest_batch(conn, batch)
        if result.inserted:
            inserted += 1
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Quipu with fixture batches")
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--database", type=Path, default=Settings().database_path)
    args = parser.parse_args()

    conn = initialize(connect(args.database))
    try:
        batches = load_fixture(args.fixture)
        inserted = seed_batches(conn, batches)
    finally:
        conn.close()

    print(f"seeded {inserted} new batches into {args.database}")


if __name__ == "__main__":
    main()
