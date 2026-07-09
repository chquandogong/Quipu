from pathlib import Path
import sqlite3


SCHEMA_VERSION = "0.13.0"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT INTO schema_meta (key, value)
VALUES ('schema_version', '0.13.0')
ON CONFLICT(key) DO UPDATE SET value = excluded.value;

CREATE TABLE IF NOT EXISTS devices (
  device_id TEXT PRIMARY KEY,
  display_name TEXT,
  hostname TEXT NOT NULL,
  model TEXT,
  cpu_model TEXT,
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

CREATE TABLE IF NOT EXISTS interventions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  investigation_id TEXT NOT NULL,
  device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  label TEXT NOT NULL,
  description TEXT NOT NULL,
  expected_effect TEXT,
  recorded_at TEXT NOT NULL,
  verification_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_interventions_investigation_time
  ON interventions(investigation_id, recorded_at ASC, id ASC);

CREATE TABLE IF NOT EXISTS agent_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL,
  label TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  rotated_at TEXT,
  revoked_at TEXT,
  last_used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_tokens_device_active
  ON agent_tokens(device_id, active);

CREATE TABLE IF NOT EXISTS investigation_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  investigation_id TEXT NOT NULL,
  author TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_investigation_notes_item_time
  ON investigation_notes(investigation_id, created_at ASC, id ASC);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.executescript(SCHEMA)
    device_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(devices)").fetchall()
    }
    if "display_name" not in device_columns:
        conn.execute("ALTER TABLE devices ADD COLUMN display_name TEXT")
    if "cpu_model" not in device_columns:
        conn.execute("ALTER TABLE devices ADD COLUMN cpu_model TEXT")
    return conn
