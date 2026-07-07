from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import socket
from typing import Any
from urllib import request


def _utc(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _root_path(root: Path, path: str) -> Path:
    return root / path.lstrip("/")


def _safe_metric_part(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def _device_id(root: Path, override: str | None) -> str:
    if override:
        return override
    machine_id = _read_text(_root_path(root, "/etc/machine-id"))
    if machine_id:
        digest = hashlib.sha256(machine_id.encode("utf-8")).hexdigest()[:16]
        return f"host-{digest}"
    hostname = _hostname(root)
    digest = hashlib.sha256(hostname.encode("utf-8")).hexdigest()[:16]
    return f"host-{digest}"


def _hostname(root: Path) -> str:
    return _read_text(_root_path(root, "/etc/hostname")) or socket.gethostname()


def _model(root: Path) -> str | None:
    return _read_text(_root_path(root, "/sys/devices/virtual/dmi/id/product_name"))


def _os_name(root: Path) -> str | None:
    os_release = _read_text(_root_path(root, "/etc/os-release"))
    if not os_release:
        return None
    for line in os_release.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def _metric(name: str, value: float, unit: str, observed_at: str) -> dict[str, Any]:
    return {
        "name": name,
        "value": round(value, 2),
        "unit": unit,
        "observed_at": observed_at,
    }


def _load_metric(root: Path, observed_at: str) -> dict[str, Any] | None:
    loadavg = _read_text(_root_path(root, "/proc/loadavg"))
    if not loadavg:
        return None
    try:
        return _metric("cpu.load_1m", float(loadavg.split()[0]), "load", observed_at)
    except (IndexError, ValueError):
        return None


def _memory_metric(root: Path, observed_at: str) -> dict[str, Any] | None:
    meminfo = _read_text(_root_path(root, "/proc/meminfo"))
    if not meminfo:
        return None
    values: dict[str, float] = {}
    for line in meminfo.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        try:
            values[key] = float(rest.strip().split()[0])
        except (IndexError, ValueError):
            continue
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if not total or available is None:
        return None
    used_percent = ((total - available) / total) * 100
    return _metric("memory.used_percent", used_percent, "percent", observed_at)


def _thermal_metrics(root: Path, observed_at: str) -> list[dict[str, Any]]:
    base = _root_path(root, "/sys/class/thermal")
    metrics: list[dict[str, Any]] = []
    for zone in sorted(base.glob("thermal_zone*")):
        raw_temp = _read_text(zone / "temp")
        if not raw_temp:
            continue
        try:
            celsius = float(raw_temp) / 1000
        except ValueError:
            continue
        sensor_type = _read_text(zone / "type") or zone.name
        metric_name = "cpu.package_temp_c" if "pkg" in sensor_type or "package" in sensor_type else None
        metric_name = metric_name or f"thermal.{_safe_metric_part(sensor_type)}.temp_c"
        metrics.append(_metric(metric_name, celsius, "celsius", observed_at))
    return metrics


def _nvme_metrics(root: Path, observed_at: str) -> list[dict[str, Any]]:
    base = _root_path(root, "/sys/class/hwmon")
    metrics: list[dict[str, Any]] = []
    for hwmon in sorted(base.glob("hwmon*")):
        name = (_read_text(hwmon / "name") or "").lower()
        if "nvme" not in name:
            continue
        for temp_input in sorted(hwmon.glob("temp*_input")):
            raw_temp = _read_text(temp_input)
            if not raw_temp:
                continue
            try:
                metrics.append(_metric("nvme.temp_c", float(raw_temp) / 1000, "celsius", observed_at))
                break
            except ValueError:
                continue
    return metrics


def _wifi_metric(root: Path, observed_at: str) -> dict[str, Any] | None:
    wireless = _read_text(_root_path(root, "/proc/net/wireless"))
    if not wireless:
        return None
    for line in wireless.splitlines():
        if ":" not in line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            return _metric("wifi.signal_dbm", float(parts[3].rstrip(".")), "dbm", observed_at)
        except ValueError:
            continue
    return None


def collect_observation(
    *,
    root: Path | str = Path("/"),
    observed_at: datetime | None = None,
    device_id: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    observed = _utc(observed_at)
    observed_iso = observed.isoformat()
    collected_device_id = _device_id(root_path, device_id)
    metrics = [
        metric
        for metric in [
            _load_metric(root_path, observed_iso),
            _memory_metric(root_path, observed_iso),
            _wifi_metric(root_path, observed_iso),
        ]
        if metric is not None
    ]
    metrics.extend(_thermal_metrics(root_path, observed_iso))
    metrics.extend(_nvme_metrics(root_path, observed_iso))

    if not metrics:
        raise RuntimeError("no readable Linux signals found")

    batch_seed = f"{collected_device_id}:{observed_iso}"
    batch_hash = hashlib.sha256(batch_seed.encode("utf-8")).hexdigest()[:12]
    return {
        "batch_id": f"collector-{batch_hash}",
        "observed_at": observed_iso,
        "device": {
            "device_id": collected_device_id,
            "hostname": _hostname(root_path),
            "model": _model(root_path),
            "os_name": _os_name(root_path),
            "kernel_version": platform.release(),
        },
        "metrics": metrics,
        "events": [],
    }


def send_observation(
    batch: dict[str, Any],
    *,
    server_url: str,
    token: str,
    timeout: float = 10,
) -> dict[str, Any]:
    url = server_url.rstrip("/") + "/api/ingest/batches"
    body = json.dumps(batch).encode("utf-8")
    http_request = request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Quipu-Agent-Token": token,
        },
    )
    with request.urlopen(http_request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
