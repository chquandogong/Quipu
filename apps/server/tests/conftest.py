from collections.abc import Iterator
from datetime import datetime, timezone
import sqlite3

import pytest

from quipu_server.contracts import DeviceIn, EventIn, MetricSampleIn, ObservationBatchIn
from quipu_server.db import connect, initialize


@pytest.fixture()
def conn(tmp_path) -> Iterator[sqlite3.Connection]:
    db_path = tmp_path / "quipu.sqlite3"
    connection = initialize(connect(db_path))
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture()
def sample_batch() -> ObservationBatchIn:
    observed_at = datetime(2026, 7, 7, 3, 0, tzinfo=timezone.utc)
    return ObservationBatchIn(
        batch_id="batch-001",
        observed_at=observed_at,
        device=DeviceIn(
            device_id="thinkpad-p1",
            display_name="Dev P1",
            hostname="dev-p1",
            model="ThinkPad P1",
            cpu_model="Intel Core Ultra 5 125H",
            os_name="Ubuntu 24.04",
            kernel_version="6.14.0",
        ),
        metrics=[
            MetricSampleIn(
                name="cpu.package_temp_c",
                value=63.2,
                unit="celsius",
                observed_at=observed_at,
            ),
            MetricSampleIn(
                name="cpu.load_1m",
                value=0.91,
                unit="load",
                observed_at=observed_at,
            ),
        ],
        events=[
            EventIn(
                category="thermal",
                severity="warning",
                source="kernel",
                message_summary="CPU package exceeded normal range",
                raw_ref="journalctl:-k:abc123",
                observed_at=observed_at,
            )
        ],
    )
