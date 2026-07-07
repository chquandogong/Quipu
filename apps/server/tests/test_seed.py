from pathlib import Path

from quipu_server.db import connect, initialize
from quipu_server.repository import list_device_snapshots
from quipu_server.seed import load_fixture, seed_batches


def test_load_fixture_and_seed_batches(tmp_path: Path) -> None:
    fixture_path = Path(__file__).parents[3] / "fixtures" / "ingest" / "team-sample.json"
    batches = load_fixture(fixture_path)
    conn = initialize(connect(tmp_path / "seed.sqlite3"))

    inserted = seed_batches(conn, batches)
    snapshots = list_device_snapshots(conn)

    assert inserted == 3
    assert len(snapshots) == 3
