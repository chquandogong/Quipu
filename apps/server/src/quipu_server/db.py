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
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.executescript(SCHEMA)
    return conn
