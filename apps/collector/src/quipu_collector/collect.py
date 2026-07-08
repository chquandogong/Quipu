from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
from typing import Any, Callable
from urllib import request


CommandRunner = Callable[[list[str]], str | None]

THERMAL_EVENT_PATTERNS = (
    "thermal thrott",
    "clock throttled",
    "above threshold",
    "critical temperature",
    "temperature above threshold",
)

NETWORK_EVENT_PATTERNS = (
    "disconnect",
    "reconnect",
    "carrier",
    "supplicant",
    "deauth",
    "dhcp",
    "link is down",
    "link is up",
    "state change",
)

STORAGE_EVENT_PATTERNS = (
    "i/o error",
    "i/o timeout",
    "reset controller",
    "media error",
    "smart",
    "ext4-fs error",
    "buffer i/o",
    "read error",
    "write error",
)

POWER_EVENT_PATTERNS = (
    "battery",
    "ac offline",
    "ac adapter",
    "power_supply",
    "critical low",
    "low battery",
    "discharge rate",
    "power management",
)


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


def _event(
    *,
    category: str,
    severity: str,
    source: str,
    message_summary: str,
    raw_ref: str,
    observed_at: str,
) -> dict[str, Any]:
    clean_summary = " ".join(message_summary.split())[:260]
    fingerprint_seed = f"{category}:{source}:{clean_summary}:{observed_at}"
    fingerprint = hashlib.sha256(fingerprint_seed.encode("utf-8")).hexdigest()[:12]
    return {
        "category": category,
        "severity": severity,
        "source": source,
        "message_summary": clean_summary,
        "raw_ref": raw_ref,
        "observed_at": observed_at,
        "fingerprint": f"{category}-{_safe_metric_part(source)}-{fingerprint}",
    }


def _line_time_and_message(line: str, fallback_observed_at: str) -> tuple[str, str]:
    stripped = line.strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2}T\S+)\s+(.*)$", stripped)
    if not match:
        return fallback_observed_at, stripped
    try:
        observed = _utc(datetime.fromisoformat(match.group(1))).isoformat()
    except ValueError:
        observed = fallback_observed_at
    return observed, match.group(2)


def _strip_source_prefix(message: str, source: str) -> str:
    return re.sub(rf"^{re.escape(source)}:\s*", "", message, flags=re.IGNORECASE)


def _classify_event_line(
    line: str,
    *,
    default_source: str,
    raw_ref: str,
    fallback_observed_at: str,
) -> dict[str, Any] | None:
    observed_at, message = _line_time_and_message(line, fallback_observed_at)
    lower = message.lower()
    if default_source == "kernel" and any(pattern in lower for pattern in THERMAL_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, "kernel")
        severity = "critical" if "critical" in lower else "warning"
        return _event(
            category="thermal",
            severity=severity,
            source="kernel",
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if default_source == "kernel" and any(pattern in lower for pattern in STORAGE_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, "kernel")
        severity = "critical" if "critical" in lower or "failed" in lower else "warning"
        return _event(
            category="storage",
            severity=severity,
            source="kernel",
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if default_source == "kernel" and any(pattern in lower for pattern in POWER_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, "kernel")
        severity = "critical" if "critical" in lower else "warning"
        return _event(
            category="power",
            severity=severity,
            source="kernel",
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if default_source == "NetworkManager" and any(pattern in lower for pattern in NETWORK_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, "NetworkManager")
        return _event(
            category="network",
            severity="warning",
            source="NetworkManager",
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    return None


def _events_from_text(
    text: str | None,
    *,
    default_source: str,
    raw_ref: str,
    fallback_observed_at: str,
) -> list[dict[str, Any]]:
    if not text:
        return []
    events: list[dict[str, Any]] = []
    for line in text.splitlines()[-120:]:
        event = _classify_event_line(
            line,
            default_source=default_source,
            raw_ref=raw_ref,
            fallback_observed_at=fallback_observed_at,
        )
        if event:
            events.append(event)
    return events[-20:]


def _run_command(args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            check=False,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _event_logs(root: Path, observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    sources = [
        ("kernel", "var/log/quipu/kernel.log"),
        ("kernel", "var/log/kern.log"),
        ("kernel", "var/log/messages"),
        ("NetworkManager", "var/log/quipu/networkmanager.log"),
        ("NetworkManager", "var/log/syslog"),
    ]
    events: list[dict[str, Any]] = []
    for source, relative_path in sources:
        events.extend(
            _events_from_text(
                _read_text(root / relative_path),
                default_source=source,
                raw_ref=relative_path,
                fallback_observed_at=observed_at,
            )
        )

    if root == Path("/"):
        runner = command_runner or _run_command
        events.extend(
            _events_from_text(
                runner(["journalctl", "--since", "-60min", "--no-pager", "-o", "short-iso", "-k"]),
                default_source="kernel",
                raw_ref="journalctl -k --since -60min",
                fallback_observed_at=observed_at,
            )
        )
        events.extend(
            _events_from_text(
                runner(["journalctl", "--since", "-60min", "--no-pager", "-o", "short-iso", "-u", "NetworkManager"]),
                default_source="NetworkManager",
                raw_ref="journalctl -u NetworkManager --since -60min",
                fallback_observed_at=observed_at,
            )
        )

    unique: dict[str, dict[str, Any]] = {}
    for event in events:
        unique[event["fingerprint"]] = event
    return sorted(unique.values(), key=lambda event: event["observed_at"])[-20:]


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


def _disk_metric(root: Path, observed_at: str) -> dict[str, Any] | None:
    try:
        usage = shutil.disk_usage(root)
    except OSError:
        return None
    if usage.total <= 0:
        return None
    used_percent = ((usage.total - usage.free) / usage.total) * 100
    return _metric("disk.root_used_percent", used_percent, "percent", observed_at)


def _parse_metric_number(value: str) -> float | None:
    hex_match = re.search(r"0x[0-9a-fA-F]+", value)
    if hex_match:
        try:
            return float(int(hex_match.group(0), 16))
        except ValueError:
            return None
    number_match = re.search(r"-?\d+(?:\.\d+)?", value)
    if not number_match:
        return None
    try:
        return float(number_match.group(0))
    except ValueError:
        return None


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


def _fan_metrics(root: Path, observed_at: str) -> list[dict[str, Any]]:
    base = _root_path(root, "/sys/class/hwmon")
    for hwmon in sorted(base.glob("hwmon*")):
        for fan_input in sorted(hwmon.glob("fan*_input")):
            raw_rpm = _read_text(fan_input)
            if raw_rpm is None:
                continue
            rpm = _parse_metric_number(raw_rpm)
            if rpm is not None and rpm >= 0:
                return [_metric("fan.rpm", rpm, "rpm", observed_at)]
    return []


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


def _nvme_health_values(controller: Path) -> dict[str, float]:
    aliases = {
        "critical_warning": "critical_warning",
        "critical_warning_raw": "critical_warning",
        "available_spare": "available_spare",
        "percentage_used": "percentage_used",
        "media_errors": "media_errors",
        "media_and_data_integrity_errors": "media_errors",
    }
    values: dict[str, float] = {}
    for file_name, value_name in aliases.items():
        raw_value = _read_text(controller / file_name)
        if raw_value is None:
            continue
        parsed = _parse_metric_number(raw_value)
        if parsed is not None:
            values[value_name] = parsed

    smart_log = _read_text(controller / "smart_log")
    if smart_log:
        for line in smart_log.splitlines():
            if ":" not in line and "=" not in line:
                continue
            separator = ":" if ":" in line else "="
            raw_key, raw_value = line.split(separator, 1)
            normalized_key = _safe_metric_part(raw_key)
            value_name = aliases.get(normalized_key)
            if not value_name:
                continue
            parsed = _parse_metric_number(raw_value)
            if parsed is not None:
                values.setdefault(value_name, parsed)
    return values


def _nvme_health_metrics(root: Path, observed_at: str) -> list[dict[str, Any]]:
    base = _root_path(root, "/sys/class/nvme")
    metric_specs = {
        "critical_warning": ("nvme.critical_warning", "boolean"),
        "available_spare": ("nvme.available_spare_percent", "percent"),
        "percentage_used": ("nvme.percentage_used_percent", "percent"),
        "media_errors": ("nvme.media_errors", "count"),
    }
    metrics_by_name: dict[str, dict[str, Any]] = {}
    for controller in sorted(base.glob("nvme*")):
        for value_name, value in _nvme_health_values(controller).items():
            metric_name, unit = metric_specs[value_name]
            if metric_name not in metrics_by_name:
                metrics_by_name[metric_name] = _metric(metric_name, value, unit, observed_at)
    return list(metrics_by_name.values())


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


def _power_supply_metrics(root: Path, observed_at: str) -> list[dict[str, Any]]:
    base = _root_path(root, "/sys/class/power_supply")
    metrics: list[dict[str, Any]] = []
    battery_recorded = False
    ac_recorded = False
    for supply in sorted(base.glob("*")):
        supply_type = (_read_text(supply / "type") or "").strip().lower()
        if supply_type == "battery" and not battery_recorded:
            raw_capacity = _read_text(supply / "capacity")
            if raw_capacity:
                try:
                    metrics.append(_metric("battery.capacity_percent", float(raw_capacity), "percent", observed_at))
                    battery_recorded = True
                except ValueError:
                    pass
        if supply_type in {"mains", "usb", "usb_c", "usb-c"} and not ac_recorded:
            raw_online = _read_text(supply / "online")
            if raw_online is None:
                continue
            try:
                metrics.append(_metric("battery.ac_online", 1.0 if float(raw_online) > 0 else 0.0, "boolean", observed_at))
                ac_recorded = True
            except ValueError:
                continue
    return metrics


def collect_observation(
    *,
    root: Path | str = Path("/"),
    observed_at: datetime | None = None,
    device_id: str | None = None,
    command_runner: CommandRunner | None = None,
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
            _disk_metric(root_path, observed_iso),
            _wifi_metric(root_path, observed_iso),
        ]
        if metric is not None
    ]
    metrics.extend(_thermal_metrics(root_path, observed_iso))
    metrics.extend(_nvme_metrics(root_path, observed_iso))
    metrics.extend(_fan_metrics(root_path, observed_iso))
    metrics.extend(_nvme_health_metrics(root_path, observed_iso))
    metrics.extend(_power_supply_metrics(root_path, observed_iso))
    events = _event_logs(root_path, observed_iso, command_runner)

    if not metrics and not events:
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
        "events": events,
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
