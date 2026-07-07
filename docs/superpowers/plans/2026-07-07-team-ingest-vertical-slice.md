# Team Ingest Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first end-to-end Quipu slice: accept health batches from multiple simulated machines, persist them in SQLite, expose a fleet overview API, and render a practical team dashboard.

**Architecture:** A Python FastAPI server owns ingestion, SQLite persistence, and rule-based fleet analysis. A Vite React UI reads the server API and shows operational fleet status. Real Linux collectors are outside this first slice; this plan uses deterministic fixture batches that match the future agent contract.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLite via the Python standard library, pytest, Vite, React, TypeScript, Vitest.

---

## Scope

This plan implements a working vertical slice for a small team deployment:

- Server accepts signed-by-header development batches from at least three devices.
- Server stores devices, batches, metric samples, and events in SQLite WAL mode.
- Server deduplicates repeated batches.
- Server computes fleet risk from current metrics, stale devices, and recent events.
- Web UI shows team status, device cards/table, latest evidence, and degraded states.
- Fixture data proves thermal, graphics/session, storage, network, update, reboot, and unclean-shutdown categories can flow through the system.

Deferred beyond this plan:

- Native Linux agent binary.
- Device enrollment UI.
- Postgres.
- AI summaries.
- Remote command execution.
- Authentication beyond a development ingest token.

## File Structure

Create this structure:

```text
apps/
├── server/
│   ├── pyproject.toml
│   ├── src/quipu_server/
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── app.py
│   │   ├── contracts.py
│   │   ├── db.py
│   │   ├── repository.py
│   │   ├── seed.py
│   │   └── settings.py
│   └── tests/
│       ├── conftest.py
│       ├── test_analysis.py
│       ├── test_api.py
│       ├── test_contracts.py
│       ├── test_repository.py
│       └── test_seed.py
├── web/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.test.tsx
│       ├── App.tsx
│       ├── api.ts
│       ├── main.tsx
│       ├── styles.css
│       └── types.ts
fixtures/
└── ingest/
    └── team-sample.json
scripts/
└── dev-server.sh
```

Responsibilities:

- `contracts.py`: Pydantic request/response contracts shared by ingestion and tests.
- `db.py`: SQLite connection and schema initialization only.
- `repository.py`: database writes and reads with no HTTP concerns.
- `analysis.py`: deterministic fleet risk and finding rules.
- `app.py`: FastAPI routes, request validation, and dependency wiring.
- `seed.py`: fixture ingestion helper for local demos.
- `apps/web/src/*`: API client and dashboard UI.
- `fixtures/ingest/team-sample.json`: deterministic three-device dataset.

---

### Task 1: Server Package Shell

**Files:**
- Create: `apps/server/pyproject.toml`
- Create: `apps/server/src/quipu_server/__init__.py`
- Create: `apps/server/src/quipu_server/settings.py`
- Create: `apps/server/tests/test_settings.py`

- [ ] **Step 1: Create the Python project file**

Create `apps/server/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=70", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "quipu-server"
version = "0.1.0"
description = "Self-hosted team workstation health investigator server"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115,<1.0",
  "pydantic>=2.8,<3.0",
  "uvicorn[standard]>=0.30,<1.0"
]

[project.optional-dependencies]
test = [
  "httpx>=0.27,<1.0",
  "pytest>=8.2,<9.0"
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Write the failing settings test**

Create `apps/server/tests/test_settings.py`:

```python
from pathlib import Path

from quipu_server.settings import Settings


def test_settings_uses_local_sqlite_default() -> None:
    settings = Settings()

    assert settings.database_path == Path("data/quipu.sqlite3")
    assert settings.dev_agent_token == "dev-token"
```

- [ ] **Step 3: Run the test and verify it fails because the package is missing**

Run:

```bash
cd apps/server
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest tests/test_settings.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'quipu_server'`.

- [ ] **Step 4: Implement the package shell**

Create `apps/server/src/quipu_server/__init__.py`:

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `apps/server/src/quipu_server/settings.py`:

```python
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(os.environ.get("QUIPU_DATABASE_PATH", "data/quipu.sqlite3"))
    dev_agent_token: str = os.environ.get("QUIPU_DEV_AGENT_TOKEN", "dev-token")
```

- [ ] **Step 5: Run the test and verify it passes**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_settings.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/server/pyproject.toml apps/server/src/quipu_server/__init__.py apps/server/src/quipu_server/settings.py apps/server/tests/test_settings.py
git commit -m "build(server): add python package shell"
```

---

### Task 2: Ingestion Contracts

**Files:**
- Create: `apps/server/tests/test_contracts.py`
- Create: `apps/server/src/quipu_server/contracts.py`

- [ ] **Step 1: Write the failing contract tests**

Create `apps/server/tests/test_contracts.py`:

```python
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from quipu_server.contracts import DeviceIn, EventIn, MetricSampleIn, ObservationBatchIn


def test_observation_batch_accepts_minimal_valid_payload() -> None:
    observed_at = datetime(2026, 7, 7, 3, 0, tzinfo=timezone.utc)

    batch = ObservationBatchIn(
        batch_id="batch-001",
        observed_at=observed_at,
        device=DeviceIn(
            device_id="thinkpad-p1",
            hostname="dev-p1",
            model="ThinkPad P1",
            os_name="Ubuntu 24.04",
            kernel_version="6.14.0",
        ),
        metrics=[
            MetricSampleIn(
                name="cpu.package_temp_c",
                value=63.2,
                unit="celsius",
                observed_at=observed_at,
            )
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

    assert batch.device.device_id == "thinkpad-p1"
    assert batch.metrics[0].name == "cpu.package_temp_c"
    assert batch.events[0].category == "thermal"


def test_batch_requires_at_least_one_metric_or_event() -> None:
    observed_at = datetime(2026, 7, 7, 3, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        ObservationBatchIn(
            batch_id="empty",
            observed_at=observed_at,
            device=DeviceIn(device_id="x", hostname="x"),
            metrics=[],
            events=[],
        )
```

- [ ] **Step 2: Run tests and verify they fail because contracts are missing**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_contracts.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'quipu_server.contracts'`.

- [ ] **Step 3: Implement contracts**

Create `apps/server/src/quipu_server/contracts.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


EventCategory = Literal[
    "thermal",
    "graphics",
    "storage",
    "network",
    "update",
    "reboot",
    "power",
    "memory",
    "unknown",
]

Severity = Literal["info", "warning", "critical"]


class DeviceIn(BaseModel):
    device_id: str = Field(min_length=1, max_length=96)
    hostname: str = Field(min_length=1, max_length=128)
    model: str | None = Field(default=None, max_length=160)
    os_name: str | None = Field(default=None, max_length=120)
    kernel_version: str | None = Field(default=None, max_length=120)

    @field_validator("device_id", "hostname")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped


class MetricSampleIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    value: float
    unit: str = Field(min_length=1, max_length=48)
    observed_at: datetime


class EventIn(BaseModel):
    category: EventCategory
    severity: Severity
    source: str = Field(min_length=1, max_length=80)
    message_summary: str = Field(min_length=1, max_length=500)
    raw_ref: str | None = Field(default=None, max_length=500)
    observed_at: datetime
    fingerprint: str | None = Field(default=None, max_length=128)


class ObservationBatchIn(BaseModel):
    batch_id: str = Field(min_length=1, max_length=128)
    observed_at: datetime
    device: DeviceIn
    metrics: list[MetricSampleIn] = Field(default_factory=list)
    events: list[EventIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_signal(self) -> "ObservationBatchIn":
        if not self.metrics and not self.events:
            raise ValueError("batch must include at least one metric or event")
        return self
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/server/src/quipu_server/contracts.py apps/server/tests/test_contracts.py
git commit -m "feat(server): define ingest contracts"
```

---

### Task 3: SQLite Repository

**Files:**
- Create: `apps/server/tests/conftest.py`
- Create: `apps/server/tests/test_repository.py`
- Create: `apps/server/src/quipu_server/db.py`
- Create: `apps/server/src/quipu_server/repository.py`

- [ ] **Step 1: Write test fixtures**

Create `apps/server/tests/conftest.py`:

```python
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
            hostname="dev-p1",
            model="ThinkPad P1",
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
```

- [ ] **Step 2: Write failing repository tests**

Create `apps/server/tests/test_repository.py`:

```python
from datetime import datetime, timezone

from quipu_server.repository import ingest_batch, list_device_snapshots


def test_ingest_batch_persists_device_metrics_and_events(conn, sample_batch) -> None:
    result = ingest_batch(conn, sample_batch, received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc))

    assert result.inserted is True
    assert result.metrics_inserted == 2
    assert result.events_inserted == 1

    snapshots = list_device_snapshots(conn)
    assert len(snapshots) == 1
    assert snapshots[0]["device"]["device_id"] == "thinkpad-p1"
    assert snapshots[0]["latest_metrics"]["cpu.package_temp_c"]["value"] == 63.2
    assert snapshots[0]["recent_events"][0]["category"] == "thermal"


def test_ingest_batch_is_idempotent_by_device_and_batch_id(conn, sample_batch) -> None:
    received_at = datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc)

    first = ingest_batch(conn, sample_batch, received_at=received_at)
    second = ingest_batch(conn, sample_batch, received_at=received_at)

    assert first.inserted is True
    assert second.inserted is False
    assert second.metrics_inserted == 0
    assert second.events_inserted == 0
```

- [ ] **Step 3: Run repository tests and verify failure**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_repository.py -v
```

Expected: FAIL because `quipu_server.db` or `quipu_server.repository` is missing.

- [ ] **Step 4: Implement SQLite schema**

Create `apps/server/src/quipu_server/db.py`:

```python
from pathlib import Path
import sqlite3


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS devices (
  device_id TEXT PRIMARY KEY,
  hostname TEXT NOT NULL,
  model TEXT,
  os_name TEXT,
  kernel_version TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS batches (
  device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
  batch_id TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  PRIMARY KEY (device_id, batch_id)
);

CREATE TABLE IF NOT EXISTS metric_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
  batch_id TEXT NOT NULL,
  name TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  UNIQUE (device_id, batch_id, name, observed_at)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
  batch_id TEXT NOT NULL,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  source TEXT NOT NULL,
  message_summary TEXT NOT NULL,
  raw_ref TEXT,
  observed_at TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  UNIQUE (device_id, fingerprint, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_metric_samples_device_name_time
  ON metric_samples(device_id, name, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_device_time
  ON events(device_id, observed_at DESC);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.executescript(SCHEMA)
    return conn
```

- [ ] **Step 5: Implement repository**

Create `apps/server/src/quipu_server/repository.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import sqlite3
from typing import Any

from quipu_server.contracts import EventIn, ObservationBatchIn


@dataclass(frozen=True)
class IngestResult:
    inserted: bool
    metrics_inserted: int
    events_inserted: int


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _event_fingerprint(event: EventIn) -> str:
    if event.fingerprint:
        return event.fingerprint
    raw = "|".join(
        [
            event.category,
            event.severity,
            event.source,
            event.message_summary,
            _iso(event.observed_at),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def ingest_batch(
    conn: sqlite3.Connection,
    batch: ObservationBatchIn,
    *,
    received_at: datetime | None = None,
) -> IngestResult:
    received_at = received_at or datetime.now(timezone.utc)
    received_iso = _iso(received_at)
    observed_iso = _iso(batch.observed_at)

    with conn:
        conn.execute(
            """
            INSERT INTO devices (
              device_id, hostname, model, os_name, kernel_version, first_seen_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
              hostname = excluded.hostname,
              model = excluded.model,
              os_name = excluded.os_name,
              kernel_version = excluded.kernel_version,
              last_seen_at = excluded.last_seen_at
            """,
            (
                batch.device.device_id,
                batch.device.hostname,
                batch.device.model,
                batch.device.os_name,
                batch.device.kernel_version,
                received_iso,
                received_iso,
            ),
        )

        batch_cursor = conn.execute(
            """
            INSERT OR IGNORE INTO batches (device_id, batch_id, observed_at, received_at)
            VALUES (?, ?, ?, ?)
            """,
            (batch.device.device_id, batch.batch_id, observed_iso, received_iso),
        )
        if batch_cursor.rowcount == 0:
            return IngestResult(inserted=False, metrics_inserted=0, events_inserted=0)

        metrics_inserted = 0
        for metric in batch.metrics:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO metric_samples (
                  device_id, batch_id, name, value, unit, observed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.device.device_id,
                    batch.batch_id,
                    metric.name,
                    metric.value,
                    metric.unit,
                    _iso(metric.observed_at),
                ),
            )
            metrics_inserted += cursor.rowcount

        events_inserted = 0
        for event in batch.events:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO events (
                  device_id, batch_id, category, severity, source, message_summary,
                  raw_ref, observed_at, fingerprint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.device.device_id,
                    batch.batch_id,
                    event.category,
                    event.severity,
                    event.source,
                    event.message_summary,
                    event.raw_ref,
                    _iso(event.observed_at),
                    _event_fingerprint(event),
                ),
            )
            events_inserted += cursor.rowcount

    return IngestResult(
        inserted=True,
        metrics_inserted=metrics_inserted,
        events_inserted=events_inserted,
    )


def list_device_snapshots(conn: sqlite3.Connection, *, recent_event_limit: int = 8) -> list[dict[str, Any]]:
    devices = conn.execute(
        """
        SELECT device_id, hostname, model, os_name, kernel_version, first_seen_at, last_seen_at
        FROM devices
        ORDER BY hostname ASC
        """
    ).fetchall()

    snapshots: list[dict[str, Any]] = []
    for device in devices:
        device_id = device["device_id"]
        metric_rows = conn.execute(
            """
            SELECT ms.name, ms.value, ms.unit, ms.observed_at
            FROM metric_samples ms
            INNER JOIN (
              SELECT name, MAX(observed_at) AS observed_at
              FROM metric_samples
              WHERE device_id = ?
              GROUP BY name
            ) latest
              ON latest.name = ms.name AND latest.observed_at = ms.observed_at
            WHERE ms.device_id = ?
            ORDER BY ms.name ASC
            """,
            (device_id, device_id),
        ).fetchall()
        event_rows = conn.execute(
            """
            SELECT category, severity, source, message_summary, raw_ref, observed_at, fingerprint
            FROM events
            WHERE device_id = ?
            ORDER BY observed_at DESC
            LIMIT ?
            """,
            (device_id, recent_event_limit),
        ).fetchall()
        snapshots.append(
            {
                "device": dict(device),
                "latest_metrics": {
                    row["name"]: {
                        "value": row["value"],
                        "unit": row["unit"],
                        "observed_at": row["observed_at"],
                    }
                    for row in metric_rows
                },
                "recent_events": [dict(row) for row in event_rows],
            }
        )
    return snapshots
```

- [ ] **Step 6: Run repository tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_repository.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/server/src/quipu_server/db.py apps/server/src/quipu_server/repository.py apps/server/tests/conftest.py apps/server/tests/test_repository.py
git commit -m "feat(server): persist ingest batches in sqlite"
```

---

### Task 4: Rule-Based Fleet Analysis

**Files:**
- Create: `apps/server/tests/test_analysis.py`
- Create: `apps/server/src/quipu_server/analysis.py`

- [ ] **Step 1: Write failing analysis tests**

Create `apps/server/tests/test_analysis.py`:

```python
from datetime import datetime, timezone

from quipu_server.analysis import build_fleet_overview


def test_fleet_overview_marks_hot_device_warning() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "hot",
                "hostname": "hotbox",
                "model": "Thin Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "cpu.package_temp_c": {
                    "value": 82.0,
                    "unit": "celsius",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                }
            },
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["risk_level"] == "warning"
    assert overview["devices"][0]["findings"][0]["category"] == "thermal"


def test_fleet_overview_marks_stale_device() -> None:
    now = datetime(2026, 7, 7, 3, 30, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "stale",
                "hostname": "offline-dev",
                "model": None,
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:00:00+00:00",
            },
            "latest_metrics": {},
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)

    assert overview["summary"]["stale"] == 1
    assert overview["devices"][0]["risk_level"] == "stale"
```

- [ ] **Step 2: Run analysis tests and verify failure**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_analysis.py -v
```

Expected: FAIL because `quipu_server.analysis` is missing.

- [ ] **Step 3: Implement analysis rules**

Create `apps/server/src/quipu_server/analysis.py`:

```python
from datetime import datetime, timezone
from typing import Any


RISK_ORDER = {"healthy": 0, "warning": 1, "critical": 2, "stale": 3}


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _metric_value(snapshot: dict[str, Any], name: str) -> float | None:
    metric = snapshot["latest_metrics"].get(name)
    if not metric:
        return None
    return float(metric["value"])


def _finding(category: str, title: str, evidence: str, confidence: str) -> dict[str, str]:
    return {
        "category": category,
        "title": title,
        "evidence": evidence,
        "confidence": confidence,
    }


def classify_snapshot(snapshot: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    device = snapshot["device"]
    findings: list[dict[str, str]] = []
    risk_level = "healthy"

    last_seen = _parse_time(device["last_seen_at"])
    stale_minutes = (now - last_seen).total_seconds() / 60
    if stale_minutes > 10:
        findings.append(
            _finding(
                "agent",
                "Device data is stale",
                f"Last batch was received {stale_minutes:.0f} minutes ago.",
                "high",
            )
        )
        risk_level = "stale"

    package_temp = _metric_value(snapshot, "cpu.package_temp_c")
    if package_temp is not None and package_temp >= 90:
        findings.append(
            _finding(
                "thermal",
                "CPU package temperature is critical",
                f"Latest CPU package temperature is {package_temp:.1f}C.",
                "high",
            )
        )
        risk_level = "critical"
    elif package_temp is not None and package_temp >= 78 and risk_level != "stale":
        findings.append(
            _finding(
                "thermal",
                "CPU package temperature is elevated",
                f"Latest CPU package temperature is {package_temp:.1f}C.",
                "medium",
            )
        )
        risk_level = "warning"

    load_1m = _metric_value(snapshot, "cpu.load_1m")
    if load_1m is not None and load_1m >= 4 and risk_level == "healthy":
        findings.append(
            _finding(
                "load",
                "Load average is elevated",
                f"Latest 1 minute load average is {load_1m:.2f}.",
                "medium",
            )
        )
        risk_level = "warning"

    for event in snapshot["recent_events"]:
        if event["severity"] == "critical" and risk_level != "stale":
            findings.append(
                _finding(
                    event["category"],
                    "Critical event reported",
                    event["message_summary"],
                    "high",
                )
            )
            risk_level = "critical"
            break
        if event["severity"] == "warning" and risk_level == "healthy":
            findings.append(
                _finding(
                    event["category"],
                    "Warning event reported",
                    event["message_summary"],
                    "medium",
                )
            )
            risk_level = "warning"

    return {
        "device": device,
        "latest_metrics": snapshot["latest_metrics"],
        "recent_events": snapshot["recent_events"],
        "risk_level": risk_level,
        "findings": findings,
    }


def build_fleet_overview(snapshots: list[dict[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    devices = [classify_snapshot(snapshot, now=now) for snapshot in snapshots]
    summary = {
        "total": len(devices),
        "healthy": 0,
        "warning": 0,
        "critical": 0,
        "stale": 0,
    }
    for device in devices:
        summary[device["risk_level"]] += 1

    devices.sort(key=lambda item: (-RISK_ORDER[item["risk_level"]], item["device"]["hostname"]))
    return {
        "generated_at": now.isoformat(),
        "summary": summary,
        "devices": devices,
    }
```

- [ ] **Step 4: Run analysis tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_analysis.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/server/src/quipu_server/analysis.py apps/server/tests/test_analysis.py
git commit -m "feat(server): classify fleet health risk"
```

---

### Task 5: FastAPI Ingest And Fleet API

**Files:**
- Create: `apps/server/tests/test_api.py`
- Create: `apps/server/src/quipu_server/app.py`

- [ ] **Step 1: Write failing API tests**

Create `apps/server/tests/test_api.py`:

```python
from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.app import create_app


def _payload() -> dict:
    return {
        "batch_id": "batch-001",
        "observed_at": "2026-07-07T03:00:00+00:00",
        "device": {
            "device_id": "thinkpad-p1",
            "hostname": "dev-p1",
            "model": "ThinkPad P1",
            "os_name": "Ubuntu 24.04",
            "kernel_version": "6.14.0",
        },
        "metrics": [
            {
                "name": "cpu.package_temp_c",
                "value": 63.2,
                "unit": "celsius",
                "observed_at": "2026-07-07T03:00:00+00:00",
            }
        ],
        "events": [],
    }


def test_ingest_requires_dev_token(tmp_path: Path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret"))

    response = client.post("/api/ingest/batches", json=_payload())

    assert response.status_code == 401


def test_ingest_then_fleet_overview(tmp_path: Path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret"))

    ingest = client.post(
        "/api/ingest/batches",
        json=_payload(),
        headers={"X-Quipu-Agent-Token": "secret"},
    )
    overview = client.get("/api/fleet/overview")

    assert ingest.status_code == 201
    assert ingest.json()["inserted"] is True
    assert overview.status_code == 200
    assert overview.json()["summary"]["total"] == 1
    assert overview.json()["devices"][0]["device"]["hostname"] == "dev-p1"
```

- [ ] **Step 2: Run API tests and verify failure**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_api.py -v
```

Expected: FAIL because `quipu_server.app` is missing.

- [ ] **Step 3: Implement FastAPI app**

Create `apps/server/src/quipu_server/app.py`:

```python
from pathlib import Path
import sqlite3

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from quipu_server.analysis import build_fleet_overview
from quipu_server.contracts import ObservationBatchIn
from quipu_server.db import connect, initialize
from quipu_server.repository import ingest_batch, list_device_snapshots
from quipu_server.settings import Settings


def create_app(
    *,
    database_path: Path | None = None,
    dev_agent_token: str | None = None,
) -> FastAPI:
    settings = Settings()
    db_path = database_path or settings.database_path
    token = dev_agent_token or settings.dev_agent_token
    conn = initialize(connect(db_path))

    app = FastAPI(title="Quipu Server", version="0.1.0")
    app.state.conn = conn
    app.state.dev_agent_token = token

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Quipu-Agent-Token"],
    )

    def get_conn() -> sqlite3.Connection:
        return app.state.conn

    def require_agent_token(x_quipu_agent_token: str | None = Header(default=None)) -> None:
        if x_quipu_agent_token != app.state.dev_agent_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid agent token")

    @app.on_event("shutdown")
    def close_connection() -> None:
        app.state.conn.close()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/ingest/batches", status_code=status.HTTP_201_CREATED)
    def ingest_observation_batch(
        batch: ObservationBatchIn,
        response: Response,
        _: None = Depends(require_agent_token),
        db: sqlite3.Connection = Depends(get_conn),
    ) -> dict[str, int | bool]:
        result = ingest_batch(db, batch)
        if not result.inserted:
            response.status_code = status.HTTP_200_OK
        return {
            "inserted": result.inserted,
            "metrics_inserted": result.metrics_inserted,
            "events_inserted": result.events_inserted,
        }

    @app.get("/api/fleet/overview")
    def fleet_overview(db: sqlite3.Connection = Depends(get_conn)) -> dict:
        snapshots = list_device_snapshots(db)
        return build_fleet_overview(snapshots)

    return app


app = create_app()
```

- [ ] **Step 4: Run API tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all server tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/server/src/quipu_server/app.py apps/server/tests/test_api.py
git commit -m "feat(server): expose ingest and fleet api"
```

---

### Task 6: Fixture Seed Workflow

**Files:**
- Create: `fixtures/ingest/team-sample.json`
- Create: `apps/server/src/quipu_server/seed.py`
- Create: `apps/server/tests/test_seed.py`

- [ ] **Step 1: Create the sample team fixture**

Create `fixtures/ingest/team-sample.json`:

```json
[
  {
    "batch_id": "dev-p1-20260707T030000Z",
    "observed_at": "2026-07-07T03:00:00+00:00",
    "device": {
      "device_id": "thinkpad-p1",
      "hostname": "dev-p1",
      "model": "ThinkPad P1",
      "os_name": "Ubuntu 24.04",
      "kernel_version": "6.14.0"
    },
    "metrics": [
      { "name": "cpu.package_temp_c", "value": 62.5, "unit": "celsius", "observed_at": "2026-07-07T03:00:00+00:00" },
      { "name": "cpu.load_1m", "value": 0.91, "unit": "load", "observed_at": "2026-07-07T03:00:00+00:00" },
      { "name": "nvme.temp_c", "value": 42.9, "unit": "celsius", "observed_at": "2026-07-07T03:00:00+00:00" }
    ],
    "events": [
      {
        "category": "reboot",
        "severity": "warning",
        "source": "journalctl",
        "message_summary": "Previous boot ended without a clean shutdown marker.",
        "raw_ref": "journalctl --list-boots",
        "observed_at": "2026-07-07T02:59:28+00:00",
        "fingerprint": "dev-p1-unclean-shutdown"
      }
    ]
  },
  {
    "batch_id": "xps-13-20260707T030000Z",
    "observed_at": "2026-07-07T03:00:00+00:00",
    "device": {
      "device_id": "xps-13",
      "hostname": "build-xps",
      "model": "Dell XPS 13",
      "os_name": "Fedora 42",
      "kernel_version": "6.14.4"
    },
    "metrics": [
      { "name": "cpu.package_temp_c", "value": 86.4, "unit": "celsius", "observed_at": "2026-07-07T03:00:00+00:00" },
      { "name": "cpu.load_1m", "value": 3.7, "unit": "load", "observed_at": "2026-07-07T03:00:00+00:00" },
      { "name": "wifi.signal_dbm", "value": -67, "unit": "dbm", "observed_at": "2026-07-07T03:00:00+00:00" }
    ],
    "events": [
      {
        "category": "thermal",
        "severity": "warning",
        "source": "kernel",
        "message_summary": "CPU thermal threshold event reported during compile workload.",
        "raw_ref": "journalctl -k --since '2026-07-07 11:55:00'",
        "observed_at": "2026-07-07T02:58:40+00:00",
        "fingerprint": "xps-thermal-threshold"
      },
      {
        "category": "network",
        "severity": "warning",
        "source": "NetworkManager",
        "message_summary": "Wi-Fi reconnect observed within the incident window.",
        "raw_ref": "journalctl -u NetworkManager",
        "observed_at": "2026-07-07T02:57:20+00:00",
        "fingerprint": "xps-wifi-reconnect"
      }
    ]
  },
  {
    "batch_id": "framework-20260707T030000Z",
    "observed_at": "2026-07-07T03:00:00+00:00",
    "device": {
      "device_id": "framework-13",
      "hostname": "ops-framework",
      "model": "Framework Laptop 13",
      "os_name": "Ubuntu 24.04",
      "kernel_version": "6.14.0"
    },
    "metrics": [
      { "name": "cpu.package_temp_c", "value": 58.1, "unit": "celsius", "observed_at": "2026-07-07T03:00:00+00:00" },
      { "name": "cpu.load_1m", "value": 0.42, "unit": "load", "observed_at": "2026-07-07T03:00:00+00:00" },
      { "name": "disk.root_used_percent", "value": 78.2, "unit": "percent", "observed_at": "2026-07-07T03:00:00+00:00" }
    ],
    "events": [
      {
        "category": "graphics",
        "severity": "warning",
        "source": "kernel",
        "message_summary": "Graphics session warning reported before user-visible stutter.",
        "raw_ref": "journalctl -k --grep i915",
        "observed_at": "2026-07-07T02:56:00+00:00",
        "fingerprint": "framework-graphics-warning"
      },
      {
        "category": "storage",
        "severity": "info",
        "source": "kernel",
        "message_summary": "NVMe temperature remained inside expected range.",
        "raw_ref": "journalctl -k --grep nvme",
        "observed_at": "2026-07-07T02:55:00+00:00",
        "fingerprint": "framework-nvme-normal"
      },
      {
        "category": "update",
        "severity": "info",
        "source": "apt",
        "message_summary": "Package update completed before the observation window.",
        "raw_ref": "/var/log/apt/history.log",
        "observed_at": "2026-07-07T02:40:00+00:00",
        "fingerprint": "framework-package-update"
      }
    ]
  }
]
```

- [ ] **Step 2: Write failing seed test**

Create `apps/server/tests/test_seed.py`:

```python
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
```

- [ ] **Step 3: Run seed test and verify failure**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_seed.py -v
```

Expected: FAIL because `quipu_server.seed` is missing.

- [ ] **Step 4: Implement seed helper**

Create `apps/server/src/quipu_server/seed.py`:

```python
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
```

- [ ] **Step 5: Run seed tests and all server tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

Expected: PASS.

- [ ] **Step 6: Smoke test fixture seeding**

Run:

```bash
cd apps/server
. .venv/bin/activate
python -m quipu_server.seed ../../fixtures/ingest/team-sample.json --database ../../data/quipu.sqlite3
```

Expected output includes:

```text
seeded 3 new batches into ../../data/quipu.sqlite3
```

- [ ] **Step 7: Commit**

```bash
git add fixtures/ingest/team-sample.json apps/server/src/quipu_server/seed.py apps/server/tests/test_seed.py
git commit -m "feat(server): add team sample seed data"
```

---

### Task 7: Web Dashboard

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/index.html`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/src/types.ts`
- Create: `apps/web/src/api.ts`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/App.test.tsx`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/styles.css`

- [ ] **Step 1: Create web package metadata**

Create `apps/web/package.json`:

```json
{
  "name": "quipu-web",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "preview": "vite preview --host 127.0.0.1"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "typescript": "^5.5.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^24.1.0",
    "vitest": "^2.0.0"
  }
}
```

Create `apps/web/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Quipu</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `apps/web/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": []
}
```

Create `apps/web/vite.config.ts`:

```ts
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    setupFiles: [],
  },
});
```

- [ ] **Step 2: Write failing UI test**

Create `apps/web/src/App.test.tsx`:

```tsx
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from './App';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('renders fleet devices from the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          generated_at: '2026-07-07T03:05:00+00:00',
          summary: { total: 1, healthy: 0, warning: 1, critical: 0, stale: 0 },
          devices: [
            {
              device: {
                device_id: 'xps-13',
                hostname: 'build-xps',
                model: 'Dell XPS 13',
                os_name: 'Fedora 42',
                kernel_version: '6.14.4',
                first_seen_at: '2026-07-07T02:55:00+00:00',
                last_seen_at: '2026-07-07T03:04:00+00:00',
              },
              latest_metrics: {
                'cpu.package_temp_c': { value: 86.4, unit: 'celsius', observed_at: '2026-07-07T03:00:00+00:00' },
              },
              recent_events: [],
              risk_level: 'warning',
              findings: [
                {
                  category: 'thermal',
                  title: 'CPU package temperature is elevated',
                  evidence: 'Latest CPU package temperature is 86.4C.',
                  confidence: 'medium',
                },
              ],
            },
          ],
        }),
      })),
    );

    render(<App />);

    await waitFor(() => expect(screen.getByText('build-xps')).toBeInTheDocument());
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('CPU package temperature is elevated')).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run UI test and verify failure**

Run:

```bash
cd apps/web
npm install
npm test
```

Expected: FAIL because `src/App.tsx` is missing.

- [ ] **Step 4: Implement typed API client**

Create `apps/web/src/types.ts`:

```ts
export type RiskLevel = 'healthy' | 'warning' | 'critical' | 'stale';

export type Device = {
  device_id: string;
  hostname: string;
  model: string | null;
  os_name: string | null;
  kernel_version: string | null;
  first_seen_at: string;
  last_seen_at: string;
};

export type MetricSample = {
  value: number;
  unit: string;
  observed_at: string;
};

export type EventSummary = {
  category: string;
  severity: string;
  source: string;
  message_summary: string;
  raw_ref: string | null;
  observed_at: string;
  fingerprint: string;
};

export type Finding = {
  category: string;
  title: string;
  evidence: string;
  confidence: string;
};

export type DeviceSnapshot = {
  device: Device;
  latest_metrics: Record<string, MetricSample>;
  recent_events: EventSummary[];
  risk_level: RiskLevel;
  findings: Finding[];
};

export type FleetOverview = {
  generated_at: string;
  summary: {
    total: number;
    healthy: number;
    warning: number;
    critical: number;
    stale: number;
  };
  devices: DeviceSnapshot[];
};
```

Create `apps/web/src/api.ts`:

```ts
import type { FleetOverview } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function fetchFleetOverview(): Promise<FleetOverview> {
  const response = await fetch(`${API_BASE_URL}/api/fleet/overview`);
  if (!response.ok) {
    throw new Error(`Fleet overview request failed with ${response.status}`);
  }
  return response.json() as Promise<FleetOverview>;
}
```

- [ ] **Step 5: Implement dashboard app**

Create `apps/web/src/App.tsx`:

```tsx
import { useEffect, useMemo, useState } from 'react';

import { fetchFleetOverview } from './api';
import type { DeviceSnapshot, FleetOverview, RiskLevel } from './types';
import './styles.css';

const riskLabels: Record<RiskLevel, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  critical: 'Critical',
  stale: 'Stale',
};

function metricValue(device: DeviceSnapshot, name: string): string {
  const metric = device.latest_metrics[name];
  if (!metric) return 'Unavailable';
  if (metric.unit === 'celsius') return `${metric.value.toFixed(1)}C`;
  if (metric.unit === 'percent') return `${metric.value.toFixed(1)}%`;
  return `${metric.value}`;
}

function riskClass(level: RiskLevel): string {
  return `risk risk-${level}`;
}

export default function App() {
  const [overview, setOverview] = useState<FleetOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchFleetOverview()
      .then((data) => {
        if (active) {
          setOverview(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unknown API error');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const topFindings = useMemo(() => {
    return overview?.devices.flatMap((device) =>
      device.findings.map((finding) => ({
        device: device.device.hostname,
        ...finding,
      })),
    ) ?? [];
  }, [overview]);

  if (loading) {
    return <main className="page"><p className="status">Loading fleet health...</p></main>;
  }

  if (error) {
    return (
      <main className="page">
        <h1>Quipu</h1>
        <p className="error">{error}</p>
      </main>
    );
  }

  if (!overview) {
    return (
      <main className="page">
        <h1>Quipu</h1>
        <p className="status">No fleet data available.</p>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Team workstation health</p>
          <h1>Quipu</h1>
        </div>
        <p className="generated">Generated {new Date(overview.generated_at).toLocaleString()}</p>
      </header>

      <section className="summary" aria-label="Fleet summary">
        <div><span>{overview.summary.total}</span><strong>Total</strong></div>
        <div><span>{overview.summary.critical}</span><strong>Critical</strong></div>
        <div><span>{overview.summary.warning}</span><strong>Warning</strong></div>
        <div><span>{overview.summary.stale}</span><strong>Stale</strong></div>
      </section>

      <section className="layout">
        <div className="panel">
          <div className="panel-head">
            <h2>Fleet</h2>
            <span>{overview.devices.length} devices</span>
          </div>
          <div className="device-list">
            {overview.devices.map((device) => (
              <article className="device-row" key={device.device.device_id}>
                <div>
                  <div className="device-title">
                    <strong>{device.device.hostname}</strong>
                    <span className={riskClass(device.risk_level)}>{riskLabels[device.risk_level]}</span>
                  </div>
                  <p>{device.device.model ?? 'Unknown model'} · {device.device.kernel_version ?? 'Unknown kernel'}</p>
                </div>
                <dl>
                  <div><dt>CPU</dt><dd>{metricValue(device, 'cpu.package_temp_c')}</dd></div>
                  <div><dt>Load</dt><dd>{metricValue(device, 'cpu.load_1m')}</dd></div>
                  <div><dt>NVMe</dt><dd>{metricValue(device, 'nvme.temp_c')}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </div>

        <aside className="panel">
          <div className="panel-head">
            <h2>Evidence</h2>
            <span>{topFindings.length} findings</span>
          </div>
          <div className="finding-list">
            {topFindings.length === 0 ? (
              <p className="status">No active findings.</p>
            ) : (
              topFindings.map((finding, index) => (
                <article className="finding" key={`${finding.device}-${finding.title}-${index}`}>
                  <span>{finding.device} · {finding.category} · {finding.confidence}</span>
                  <strong>{finding.title}</strong>
                  <p>{finding.evidence}</p>
                </article>
              ))
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
```

Create `apps/web/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 6: Add dashboard styling**

Create `apps/web/src/styles.css`:

```css
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f4f6fa;
  color: #162033;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

.page {
  min-height: 100vh;
  padding: 24px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-end;
  margin-bottom: 20px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #0f766e;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1, h2, p {
  margin-top: 0;
}

h1 {
  margin-bottom: 0;
  font-size: 44px;
  letter-spacing: 0;
}

h2 {
  margin-bottom: 0;
  font-size: 18px;
}

.generated,
.status,
.error {
  color: #667085;
}

.error {
  color: #b42318;
}

.summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary div,
.panel {
  background: #ffffff;
  border: 1px solid #d8dde6;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}

.summary div {
  padding: 16px;
}

.summary span {
  display: block;
  font-size: 30px;
  font-weight: 800;
}

.summary strong {
  color: #667085;
  font-size: 13px;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.6fr);
  gap: 18px;
}

.panel {
  padding: 16px;
}

.panel-head,
.device-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-head {
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ec;
  color: #667085;
}

.device-list,
.finding-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.device-row {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(260px, 0.8fr);
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #eef1f5;
}

.device-row:last-child {
  border-bottom: 0;
}

.device-row p {
  margin: 6px 0 0;
  color: #667085;
  font-size: 13px;
}

dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

dt {
  color: #667085;
  font-size: 12px;
}

dd {
  margin: 2px 0 0;
  font-weight: 800;
}

.risk {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.risk-healthy {
  background: #ecfdf3;
  color: #027a48;
}

.risk-warning {
  background: #fffaeb;
  color: #b54708;
}

.risk-critical {
  background: #fef3f2;
  color: #b42318;
}

.risk-stale {
  background: #f2f4f7;
  color: #475467;
}

.finding {
  padding: 12px;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  background: #fbfcfe;
}

.finding span {
  display: block;
  margin-bottom: 6px;
  color: #667085;
  font-size: 12px;
}

.finding strong {
  display: block;
  margin-bottom: 6px;
}

.finding p {
  margin-bottom: 0;
  color: #475467;
  font-size: 13px;
  line-height: 1.45;
}

@media (max-width: 900px) {
  .page {
    padding: 16px;
  }

  .topbar,
  .device-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary,
  .layout,
  .device-row {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Run UI tests and build**

Run:

```bash
cd apps/web
npm test
npm run build
```

Expected: PASS for tests and successful Vite build.

- [ ] **Step 8: Commit**

```bash
git add apps/web
git commit -m "feat(web): add fleet overview dashboard"
```

---

### Task 8: Local Run Script And README Update

**Files:**
- Create: `scripts/dev-server.sh`
- Modify: `README.md`
- Modify: `docs/superpowers/DASHBOARD.md`

- [ ] **Step 1: Create server run helper**

Create `scripts/dev-server.sh`:

```bash
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
```

Run:

```bash
chmod +x scripts/dev-server.sh
```

- [ ] **Step 2: Update README with local run commands**

Modify `README.md` by adding this section after the initial wedge list:

~~~markdown
## First Vertical Slice

The first implementation slice provides:

- FastAPI ingest API.
- SQLite persistence.
- Rule-based fleet overview.
- Deterministic three-device sample data.
- Vite React team dashboard.

Run the server:

```bash
scripts/dev-server.sh
```

In another terminal, run the web UI:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.
~~~

- [ ] **Step 3: Update the project dashboard work board**

Modify `docs/superpowers/DASHBOARD.md` so the work board contains:

```markdown
| State | Item | Notes |
| --- | --- | --- |
| Done | Project directory and Git repo | `/home/chquan/Quipu`, branch `main` |
| Done | Team direction selected | User selected multi-device/team scope |
| Done | Design spec | `docs/superpowers/specs/2026-07-07-team-health-investigator-design.md` |
| In progress | First vertical slice | Server ingest, SQLite, fixture data, fleet overview UI |
| Pending | Native Linux agent | Do after the first vertical slice works |
| Pending | Remote push | User said later; no remote configured yet |
```

- [ ] **Step 4: Run all verification commands**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
cd ../web
npm test
npm run build
```

Expected: all server tests pass, UI test passes, and Vite build succeeds.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/DASHBOARD.md scripts/dev-server.sh
git commit -m "docs: add first slice runbook"
```

---

## Final Verification

After all tasks:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected:

- Working tree is clean.
- Latest commits show package shell, contracts, SQLite persistence, analysis, API, fixtures, web dashboard, and runbook.

Run the local demo:

```bash
scripts/dev-server.sh
```

In another terminal:

```bash
cd apps/web
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Expected visible behavior:

- Quipu dashboard loads.
- Summary shows three total devices.
- At least one device is warning due to elevated CPU temperature.
- Evidence panel shows thermal, reboot, network, or graphics findings.
- No remote service is required.

## Plan Self-Review

Spec coverage:

- Multi-device ingest: Tasks 2, 3, 5, and 6.
- SQLite WAL storage: Task 3.
- Rule-based analysis before AI: Task 4.
- Team dashboard: Task 7.
- Lightweight self-hosted workflow: Task 8.
- Evidence-linked findings: Tasks 4 and 7.
- Native Linux collectors: intentionally outside this first slice.
- Intervention tracking: intentionally outside this first slice because a reliable first ingest and fleet overview must exist before before/after comparisons.

Placeholder scan:

- The plan uses exact file paths.
- Code-changing steps include concrete code blocks.
- Commands include expected outcomes.
- Deferred items are explicitly scoped out rather than left ambiguous.

Type consistency:

- Server returns `generated_at`, `summary`, and `devices`.
- Web `FleetOverview` type matches the server response.
- Risk levels are `healthy`, `warning`, `critical`, and `stale` in both server and web.
