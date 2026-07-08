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

GRAPHICS_EVENT_PATTERNS = (
    "gpu hang",
    "*error*",
    "atomic update failure",
    "gpu fault",
    "xid",
    "gnome-shell",
    "kwin",
    "xorg",
    "wayland",
)

UPDATE_EVENT_PATTERNS = (
    "upgrade:",
    "install:",
    "remove:",
    "dnf",
    "apt",
    "package update",
    "updated",
)

REBOOT_EVENT_PATTERNS = (
    "reboot",
    "shutdown",
    "unclean shutdown",
    "starting reboot",
    "system boot",
)

MEMORY_EVENT_PATTERNS = (
    "out of memory",
    "oom",
    "killed process",
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


def _cpu_model(root: Path) -> str | None:
    cpuinfo = _read_text(_root_path(root, "/proc/cpuinfo"))
    if cpuinfo:
        preferred_keys = ("model name", "Hardware", "Processor")
        for preferred_key in preferred_keys:
            for line in cpuinfo.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                if key.strip() == preferred_key:
                    stripped = value.strip()
                    if stripped:
                        return stripped
    if root == Path("/"):
        detected = platform.processor().strip()
        return detected or None
    return None


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


def _line_source(message: str, default_source: str) -> str:
    for source in ("kernel", "systemd", "journalctl", "apt", "dnf", "NetworkManager"):
        if re.match(rf"^{re.escape(source)}:\s*", message, flags=re.IGNORECASE):
            return source
    return default_source


def _classify_event_line(
    line: str,
    *,
    default_source: str,
    raw_ref: str,
    fallback_observed_at: str,
) -> dict[str, Any] | None:
    observed_at, message = _line_time_and_message(line, fallback_observed_at)
    source = _line_source(message, default_source)
    lower = message.lower()
    if source == "kernel" and any(pattern in lower for pattern in THERMAL_EVENT_PATTERNS):
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
    if source == "kernel" and any(pattern in lower for pattern in STORAGE_EVENT_PATTERNS):
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
    if source == "kernel" and any(pattern in lower for pattern in POWER_EVENT_PATTERNS):
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
    if source == "kernel" and any(pattern in lower for pattern in GRAPHICS_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, "kernel")
        return _event(
            category="graphics",
            severity="warning",
            source="kernel",
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if source == "kernel" and any(pattern in lower for pattern in MEMORY_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, "kernel")
        return _event(
            category="memory",
            severity="critical",
            source="kernel",
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if source in {"systemd", "journalctl"} and any(pattern in lower for pattern in REBOOT_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, source)
        return _event(
            category="reboot",
            severity="info",
            source=source,
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if source in {"apt", "dnf"} and any(pattern in lower for pattern in UPDATE_EVENT_PATTERNS):
        summary = _strip_source_prefix(message, source)
        return _event(
            category="update",
            severity="info",
            source=source,
            message_summary=summary,
            raw_ref=raw_ref,
            observed_at=observed_at,
        )
    if source == "NetworkManager" and any(pattern in lower for pattern in NETWORK_EVENT_PATTERNS):
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
        ("systemd", "var/log/quipu/system.log"),
        ("apt", "var/log/apt/history.log"),
        ("dnf", "var/log/dnf.log"),
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


def _load_metrics(root: Path, observed_at: str) -> list[dict[str, Any]]:
    loadavg = _read_text(_root_path(root, "/proc/loadavg"))
    if not loadavg:
        return []
    metrics: list[dict[str, Any]] = []
    for metric_name, index in (("cpu.load_1m", 0), ("cpu.load_5m", 1), ("cpu.load_15m", 2)):
        try:
            metrics.append(_metric(metric_name, float(loadavg.split()[index]), "load", observed_at))
        except (IndexError, ValueError):
            continue
    return metrics


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


def _cpu_topology_for_model(cpu_model: str | None) -> dict[str, float]:
    if not cpu_model:
        return {}
    normalized = cpu_model.lower()
    if re.search(r"\bultra\s+5\s+125h\b", normalized):
        return {
            "cpu.physical_cores": 14.0,
            "cpu.logical_threads": 18.0,
            "cpu.performance_cores": 4.0,
            "cpu.efficient_cores": 8.0,
            "cpu.low_power_efficient_cores": 2.0,
        }
    return {}


def _cpu_metrics(root: Path, observed_at: str, cpu_model: str | None) -> list[dict[str, Any]]:
    values = _cpu_topology_for_model(cpu_model)
    cpuinfo = _read_text(_root_path(root, "/proc/cpuinfo"))
    if cpuinfo:
        processors: set[int] = set()
        physical_core_count: float | None = None
        sibling_count: float | None = None
        physical_core_ids: set[tuple[str, str]] = set()
        current_physical_id = "0"
        for line in cpuinfo.splitlines():
            if not line.strip():
                current_physical_id = "0"
                continue
            if ":" not in line:
                continue
            key, raw_value = [part.strip() for part in line.split(":", 1)]
            if key == "processor":
                parsed = _parse_metric_number(raw_value)
                if parsed is not None:
                    processors.add(int(parsed))
            elif key == "physical id":
                current_physical_id = raw_value or "0"
            elif key == "core id":
                physical_core_ids.add((current_physical_id, raw_value or "0"))
            elif key == "cpu cores" and physical_core_count is None:
                physical_core_count = _parse_metric_number(raw_value)
            elif key == "siblings" and sibling_count is None:
                sibling_count = _parse_metric_number(raw_value)

        if processors and "cpu.logical_threads" not in values:
            values["cpu.logical_threads"] = float(len(processors))
        if physical_core_ids and "cpu.physical_cores" not in values:
            values["cpu.physical_cores"] = float(len(physical_core_ids))
        elif physical_core_count is not None and "cpu.physical_cores" not in values:
            values["cpu.physical_cores"] = physical_core_count
        if sibling_count is not None and "cpu.logical_threads" not in values:
            values["cpu.logical_threads"] = sibling_count

    return [
        _metric(name, value, "count", observed_at)
        for name, value in sorted(values.items())
        if value >= 0
    ]


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
    metrics_by_name: dict[str, dict[str, Any]] = {}
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
        metrics_by_name.setdefault(metric_name, _metric(metric_name, celsius, "celsius", observed_at))

    hwmon_base = _root_path(root, "/sys/class/hwmon")
    cpu_sensor_names = {"coretemp", "k10temp", "zenpower", "cpu_thermal"}
    for hwmon in sorted(hwmon_base.glob("hwmon*")):
        sensor_name = (_read_text(hwmon / "name") or "").strip().lower()
        if sensor_name not in cpu_sensor_names:
            continue
        for temp_input in sorted(hwmon.glob("temp*_input")):
            raw_temp = _read_text(temp_input)
            if not raw_temp:
                continue
            try:
                celsius = float(raw_temp) / 1000
            except ValueError:
                continue
            label_name = temp_input.name.replace("_input", "_label")
            label = (_read_text(hwmon / label_name) or temp_input.stem).strip()
            lower_label = label.lower()
            core_match = re.search(r"core\s*(\d+)", lower_label)
            if core_match:
                metric_name = f"cpu.core_{core_match.group(1)}.temp_c"
            elif any(token in lower_label for token in ("package", "tctl", "tdie")):
                metric_name = "cpu.package_temp_c"
            else:
                continue
            metrics_by_name.setdefault(metric_name, _metric(metric_name, celsius, "celsius", observed_at))
    return list(metrics_by_name.values())


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
    generic_recorded = False
    nvme_index = 0
    for hwmon in sorted(base.glob("hwmon*")):
        name = (_read_text(hwmon / "name") or "").lower()
        if "nvme" not in name:
            continue
        device_name = _nvme_device_name(hwmon, nvme_index)
        nvme_index += 1
        for temp_input in sorted(hwmon.glob("temp*_input")):
            raw_temp = _read_text(temp_input)
            if not raw_temp:
                continue
            try:
                celsius = float(raw_temp) / 1000
                if not generic_recorded:
                    metrics.append(_metric("nvme.temp_c", celsius, "celsius", observed_at))
                    generic_recorded = True
                metrics.append(_metric(f"nvme.{device_name}.temp_c", celsius, "celsius", observed_at))
                break
            except ValueError:
                continue
    return metrics


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json_object(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        temp_path.replace(path)
    except OSError:
        return


def _block_stat_bytes(block_device: Path) -> tuple[float, float] | None:
    raw_stat = _read_text(block_device / "stat")
    if not raw_stat:
        return None
    parts = raw_stat.split()
    if len(parts) < 7:
        return None
    try:
        read_sectors = float(parts[2])
        write_sectors = float(parts[6])
    except ValueError:
        return None
    return read_sectors * 512, write_sectors * 512


def _nvme_block_metrics(
    root: Path,
    observed_at: str,
    observed: datetime,
    state_dir: Path | None,
) -> list[dict[str, Any]]:
    base = _root_path(root, "/sys/class/block")
    metrics: list[dict[str, Any]] = []
    total_capacity = 0.0
    aggregate_read_bps = 0.0
    aggregate_write_bps = 0.0
    rate_samples = 0
    previous_state: dict[str, Any] = {}
    state_path = state_dir / "nvme-io.json" if state_dir is not None else None
    if state_path is not None:
        previous_state = _read_json_object(state_path)
    next_state: dict[str, Any] = {
        "observed_at": observed_at,
        "timestamp": observed.timestamp(),
        "devices": {},
    }

    for block_device in sorted(base.glob("nvme*n*")):
        if not re.fullmatch(r"nvme\d+n\d+", block_device.name):
            continue
        device_name = _safe_metric_part(block_device.name)
        raw_size = _read_text(block_device / "size")
        if raw_size:
            parsed_size = _parse_metric_number(raw_size)
            if parsed_size is not None and parsed_size > 0:
                capacity_bytes = parsed_size * 512
                total_capacity += capacity_bytes
                metrics.append(_metric(f"nvme.{device_name}.capacity_bytes", capacity_bytes, "bytes", observed_at))

        stat_bytes = _block_stat_bytes(block_device)
        if stat_bytes is None:
            continue
        read_bytes, write_bytes = stat_bytes
        next_state["devices"][device_name] = {
            "read_bytes": read_bytes,
            "write_bytes": write_bytes,
        }
        previous_devices = previous_state.get("devices")
        previous_device = previous_devices.get(device_name) if isinstance(previous_devices, dict) else None
        previous_timestamp = previous_state.get("timestamp")
        if not isinstance(previous_device, dict) or not isinstance(previous_timestamp, (int, float)):
            continue
        elapsed = observed.timestamp() - float(previous_timestamp)
        if elapsed <= 0:
            continue
        previous_read = previous_device.get("read_bytes")
        previous_write = previous_device.get("write_bytes")
        if not isinstance(previous_read, (int, float)) or not isinstance(previous_write, (int, float)):
            continue
        read_bps = max(0.0, read_bytes - float(previous_read)) / elapsed
        write_bps = max(0.0, write_bytes - float(previous_write)) / elapsed
        aggregate_read_bps += read_bps
        aggregate_write_bps += write_bps
        rate_samples += 1
        metrics.append(_metric(f"nvme.{device_name}.read_bytes_per_sec", read_bps, "bytes_per_sec", observed_at))
        metrics.append(_metric(f"nvme.{device_name}.write_bytes_per_sec", write_bps, "bytes_per_sec", observed_at))

    if total_capacity > 0:
        metrics.insert(0, _metric("nvme.capacity_bytes", total_capacity, "bytes", observed_at))
    if rate_samples > 0:
        metrics.insert(0, _metric("nvme.write_bytes_per_sec", aggregate_write_bps, "bytes_per_sec", observed_at))
        metrics.insert(0, _metric("nvme.read_bytes_per_sec", aggregate_read_bps, "bytes_per_sec", observed_at))
    if state_path is not None and next_state["devices"]:
        _write_json_object(state_path, next_state)
    return metrics


def _nvme_device_name(hwmon: Path, fallback_index: int) -> str:
    candidates: list[str] = []
    for path in (hwmon / "device", hwmon):
        try:
            candidates.extend(path.resolve(strict=False).parts)
        except OSError:
            continue
    for part in reversed(candidates):
        if re.fullmatch(r"nvme\d+", part):
            return _safe_metric_part(part)
    return f"nvme{fallback_index}"


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


def _wifi_link_bitrate_metrics(
    interface: str,
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    runner = command_runner or _run_command
    link = runner(["iw", "dev", interface, "link"])
    metrics: list[dict[str, Any]] = []
    generic_names = {
        "rx": "wifi.rx_bitrate_mbps",
        "tx": "wifi.tx_bitrate_mbps",
    }
    if link:
        for direction in ("rx", "tx"):
            match = re.search(rf"\b{direction}\s+bitrate:\s*([0-9.]+)\s*([GMK]?Bit/s)", link, flags=re.IGNORECASE)
            if not match:
                continue
            value = _wifi_bitrate_value_mbps(match.group(1), match.group(2))
            if value is None:
                continue
            metrics.append(_metric(f"wifi.{interface}.{direction}_bitrate_mbps", value, "mbps", observed_at))
            metrics.append(_metric(generic_names[direction], value, "mbps", observed_at))
    if metrics:
        return metrics

    iwconfig = runner(["iwconfig", interface])
    if not iwconfig:
        return []
    match = re.search(r"\bBit Rate[:=]\s*([0-9.]+)\s*([GMK]?(?:b/s|Bit/s))", iwconfig, flags=re.IGNORECASE)
    if not match:
        return []
    value = _wifi_bitrate_value_mbps(match.group(1), match.group(2))
    if value is None:
        return []
    return [
        _metric(f"wifi.{interface}.link_bitrate_mbps", value, "mbps", observed_at),
        _metric("wifi.link_bitrate_mbps", value, "mbps", observed_at),
    ]


def _wifi_bitrate_value_mbps(raw_value: str, raw_unit: str) -> float | None:
    try:
        value = float(raw_value)
    except ValueError:
        return None
    unit = raw_unit.lower()
    if unit.startswith("g"):
        value *= 1000
    elif unit.startswith("k"):
        value /= 1000
    return value
    return metrics


def _wifi_metrics(root: Path, observed_at: str, command_runner: CommandRunner | None = None) -> list[dict[str, Any]]:
    wireless = _read_text(_root_path(root, "/proc/net/wireless"))
    if not wireless:
        return []
    metrics: list[dict[str, Any]] = []
    generic_recorded = False
    generic_bitrates_recorded: set[str] = set()
    for line in wireless.splitlines():
        if ":" not in line:
            continue
        raw_interface = line.split(":", 1)[0].strip()
        interface = _safe_metric_part(raw_interface)
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            signal = float(parts[3].rstrip("."))
        except ValueError:
            continue
        if not generic_recorded:
            metrics.append(_metric("wifi.signal_dbm", signal, "dbm", observed_at))
            generic_recorded = True
        metrics.append(_metric(f"wifi.{interface}.signal_dbm", signal, "dbm", observed_at))
        for metric in _wifi_link_bitrate_metrics(raw_interface, observed_at, command_runner):
            if metric["name"].startswith(f"wifi.{raw_interface}."):
                metric["name"] = metric["name"].replace(f"wifi.{raw_interface}.", f"wifi.{interface}.", 1)
            if metric["name"] in {"wifi.rx_bitrate_mbps", "wifi.tx_bitrate_mbps", "wifi.link_bitrate_mbps"}:
                if metric["name"] in generic_bitrates_recorded:
                    continue
                generic_bitrates_recorded.add(metric["name"])
            metrics.append(metric)
    return metrics


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
    device_alias: str | None = None,
    state_dir: Path | str | None = None,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    collector_state_dir = Path(state_dir).expanduser() if state_dir is not None else None
    observed = _utc(observed_at)
    observed_iso = observed.isoformat()
    collected_device_id = _device_id(root_path, device_id)
    cpu_model = _cpu_model(root_path)
    metrics = _load_metrics(root_path, observed_iso)
    metrics.extend(_cpu_metrics(root_path, observed_iso, cpu_model))
    metrics.extend(
        metric
        for metric in [
            _memory_metric(root_path, observed_iso),
            _disk_metric(root_path, observed_iso),
        ]
        if metric is not None
    )
    metrics.extend(_wifi_metrics(root_path, observed_iso, command_runner))
    metrics.extend(_thermal_metrics(root_path, observed_iso))
    metrics.extend(_nvme_metrics(root_path, observed_iso))
    metrics.extend(_nvme_block_metrics(root_path, observed_iso, observed, collector_state_dir))
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
            "display_name": device_alias.strip() if device_alias and device_alias.strip() else None,
            "hostname": _hostname(root_path),
            "model": _model(root_path),
            "cpu_model": cpu_model,
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
