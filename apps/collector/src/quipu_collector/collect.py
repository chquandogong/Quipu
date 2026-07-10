from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
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
        if _is_windows_runtime(root):
            detected = platform.platform().strip()
            return detected or None
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


def _run_command(
    args: list[str],
    *,
    timeout: float = 2.0,
    accept_nonzero: bool = False,
) -> str | None:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0 and not accept_nonzero:
        return None
    return completed.stdout


def _run_observation_command(
    args: list[str],
    command_runner: CommandRunner | None,
    *,
    timeout: float = 2.0,
    accept_nonzero: bool = False,
) -> str | None:
    if command_runner is not None:
        return command_runner(args)
    return _run_command(args, timeout=timeout, accept_nonzero=accept_nonzero)


def _is_windows_runtime(root: Path) -> bool:
    return platform.system().lower() == "windows"


def _powershell_json(script: str, command_runner: CommandRunner | None) -> Any:
    utf8_script = (
        "$OutputEncoding = New-Object System.Text.UTF8Encoding $false;"
        "[Console]::OutputEncoding = $OutputEncoding;"
        f"{script}"
    )
    output = _run_observation_command(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", utf8_script],
        command_runner,
        timeout=15.0,
    )
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def _json_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _windows_device_info(command_runner: CommandRunner | None) -> dict[str, str]:
    payload = _powershell_json(
        "$cs=Get-CimInstance Win32_ComputerSystem;"
        "$os=Get-CimInstance Win32_OperatingSystem;"
        "$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1;"
        "[pscustomobject]@{Model=$cs.Model;OsName=$os.Caption;CpuModel=$cpu.Name} | ConvertTo-Json -Compress",
        command_runner,
    )
    info: dict[str, str] = {}
    for item in _json_items(payload):
        for source_key, target_key in (("Model", "model"), ("OsName", "os_name"), ("CpuModel", "cpu_model")):
            value = item.get(source_key)
            if isinstance(value, str) and value.strip():
                info[target_key] = value.strip()
    if "model" not in info:
        payload = _powershell_json(
            "Get-CimInstance Win32_ComputerSystem | Select-Object Model | ConvertTo-Json -Compress",
            command_runner,
        )
        for item in _json_items(payload)[:1]:
            value = item.get("Model")
            if isinstance(value, str) and value.strip():
                info["model"] = value.strip()
    if "os_name" not in info:
        payload = _powershell_json(
            "Get-CimInstance Win32_OperatingSystem | Select-Object Caption | ConvertTo-Json -Compress",
            command_runner,
        )
        for item in _json_items(payload)[:1]:
            value = item.get("Caption")
            if isinstance(value, str) and value.strip():
                info["os_name"] = value.strip()
    if "cpu_model" not in info:
        payload = _powershell_json(
            "Get-CimInstance Win32_Processor | Select-Object -First 1 Name | ConvertTo-Json -Compress",
            command_runner,
        )
        for item in _json_items(payload)[:1]:
            value = item.get("Name")
            if isinstance(value, str) and value.strip():
                info["cpu_model"] = value.strip()
    return info


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


def _windows_event_observed_at(value: Any, fallback_observed_at: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback_observed_at
    text = value.strip()
    epoch_match = re.search(r"/Date\((\d+)", text)
    if epoch_match:
        try:
            return _utc(datetime.fromtimestamp(int(epoch_match.group(1)) / 1000, tz=timezone.utc)).isoformat()
        except (OSError, OverflowError, ValueError):
            return fallback_observed_at
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    text = re.sub(r"(\.\d{6})\d+(?=[+-]\d\d:\d\d$)", r"\1", text)
    try:
        return _utc(datetime.fromisoformat(text)).isoformat()
    except ValueError:
        return fallback_observed_at


def _windows_event_category(record: dict[str, Any]) -> str | None:
    source = str(record.get("ProviderName") or record.get("Provider") or "")
    message = str(record.get("Message") or "")
    text = f"{source} {message}".lower()
    event_id = int(_coerce_metric_number(record.get("Id")) or -1)
    if event_id in {41, 1074, 1076, 6005, 6006, 6008} or any(pattern in text for pattern in REBOOT_EVENT_PATTERNS):
        return "reboot"
    if any(pattern in text for pattern in UPDATE_EVENT_PATTERNS) or any(
        marker in text for marker in ("windowsupdate", "windows update", "servicing")
    ):
        return "update"
    if any(pattern in text for pattern in THERMAL_EVENT_PATTERNS) or any(
        marker in text for marker in ("thermal", "temperature")
    ):
        return "thermal"
    if any(pattern in text for pattern in STORAGE_EVENT_PATTERNS) or any(
        marker in text for marker in (" disk", "disk ", "stornvme", "storahci", "nvme", "ntfs", "volmgr")
    ):
        return "storage"
    if any(pattern in text for pattern in NETWORK_EVENT_PATTERNS) or any(
        marker in text for marker in ("wlan", "wi-fi", "wifi", "netwtw", "tcpip", "dhcp-client", "ndis")
    ):
        return "network"
    if any(pattern in text for pattern in GRAPHICS_EVENT_PATTERNS) or any(
        marker in text for marker in ("display", "graphics", "igfx", "nvlddmkm", "amdkmdag")
    ):
        return "graphics"
    if any(pattern in text for pattern in MEMORY_EVENT_PATTERNS) or any(
        marker in text for marker in ("resource-exhaustion", "memorydiagnostics", "memory diagnostic")
    ):
        return "memory"
    if any(pattern in text for pattern in POWER_EVENT_PATTERNS) or "power" in text:
        return "power"
    return None


def _windows_event_severity(record: dict[str, Any], category: str) -> str:
    level_name = str(record.get("LevelDisplayName") or "").lower()
    level = _coerce_metric_number(record.get("Level"))
    if "critical" in level_name or level == 1:
        return "critical"
    if "error" in level_name or level == 2:
        return "critical"
    if "warning" in level_name or level == 3:
        return "warning"
    if category in {"reboot", "update"}:
        return "info"
    return "warning"


def _windows_event_from_record(record: dict[str, Any], fallback_observed_at: str) -> dict[str, Any] | None:
    category = _windows_event_category(record)
    if category is None:
        return None
    source = str(record.get("ProviderName") or record.get("Provider") or record.get("LogName") or "Windows Event Log")
    event_id = record.get("Id")
    log_name = str(record.get("LogName") or "unknown")
    message = str(record.get("Message") or "").strip()
    if not message:
        message = f"Windows event {event_id}"
    return _event(
        category=category,
        severity=_windows_event_severity(record, category),
        source=source,
        message_summary=message,
        raw_ref=f"windows-eventlog:{log_name}:{event_id}",
        observed_at=_windows_event_observed_at(record.get("TimeCreated"), fallback_observed_at),
    )


def _windows_event_logs(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "$start=(Get-Date).AddMinutes(-60);"
        "$events=@();"
        "foreach ($log in @('System','Application')) {"
        "$events += Get-WinEvent -FilterHashtable @{LogName=$log; StartTime=$start} "
        "-MaxEvents 120 -ErrorAction SilentlyContinue"
        "};"
        "$events | Select-Object -First 160 | ForEach-Object {"
        "[pscustomobject]@{TimeCreated=$_.TimeCreated.ToUniversalTime().ToString('o');"
        "ProviderName=$_.ProviderName;Id=$_.Id;Level=$_.Level;"
        "LevelDisplayName=$_.LevelDisplayName;LogName=$_.LogName;Message=$_.Message}"
        "} | ConvertTo-Json -Compress",
        command_runner,
    )
    events = [
        event
        for event in (_windows_event_from_record(record, observed_at) for record in _json_items(payload))
        if event is not None
    ]
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
    known_topologies = (
        (
            r"\bultra\s+5\s+125h\b",
            {
                "cpu.physical_cores": 14.0,
                "cpu.logical_threads": 18.0,
                "cpu.performance_cores": 4.0,
                "cpu.efficient_cores": 8.0,
                "cpu.low_power_efficient_cores": 2.0,
            },
        ),
        (
            r"\bi5-1340p\b",
            {
                "cpu.physical_cores": 12.0,
                "cpu.logical_threads": 16.0,
                "cpu.performance_cores": 4.0,
                "cpu.efficient_cores": 8.0,
            },
        ),
    )
    for pattern, values in known_topologies:
        if re.search(pattern, normalized):
            return dict(values)
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


def _coerce_metric_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return _parse_metric_number(value)
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
    metrics_by_name: dict[str, dict[str, Any]] = {}
    generic_recorded = False
    for hwmon in sorted(base.glob("hwmon*")):
        hardware_name = _safe_metric_part(_read_text(hwmon / "name") or hwmon.name)
        for fan_input in sorted(hwmon.glob("fan*_input")):
            raw_rpm = _read_text(fan_input)
            if raw_rpm is None:
                continue
            rpm = _parse_metric_number(raw_rpm)
            if rpm is not None and rpm >= 0:
                label_path = hwmon / fan_input.name.replace("_input", "_label")
                label = _safe_metric_part(
                    _read_text(label_path) or fan_input.name.replace("_input", "")
                )
                if not generic_recorded:
                    metrics_by_name["fan.rpm"] = _metric("fan.rpm", rpm, "rpm", observed_at)
                    generic_recorded = True
                metric_name = f"fan.{hardware_name}_{label}.rpm"
                metrics_by_name.setdefault(metric_name, _metric(metric_name, rpm, "rpm", observed_at))
    return list(metrics_by_name.values())


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


def _smartctl_binary(command_runner: CommandRunner | None) -> str | None:
    if command_runner is not None:
        return "smartctl"

    candidates = [os.environ.get("QUIPU_SMARTCTL_BIN"), shutil.which("smartctl")]
    if platform.system().lower() == "windows":
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env_name)
            if base:
                candidates.append(str(Path(base) / "smartmontools" / "bin" / "smartctl.exe"))

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _smartctl_json(
    args: list[str],
    command_runner: CommandRunner | None,
) -> dict[str, Any]:
    binary = _smartctl_binary(command_runner)
    if not binary:
        return {}
    output = _run_observation_command(
        [binary, *args],
        command_runner,
        timeout=20.0,
        accept_nonzero=True,
    )
    if not output:
        return {}
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _nested_metric_number(payload: dict[str, Any], *path: str) -> float | None:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return _coerce_metric_number(value)


def _smartctl_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    scan = _smartctl_json(["--scan-open", "--json"], command_runner)
    devices = scan.get("devices")
    if not isinstance(devices, list):
        return []

    metric_specs = {
        "smart_passed": ("smart_passed", "boolean"),
        "critical_warning": ("critical_warning", "boolean"),
        "available_spare": ("available_spare_percent", "percent"),
        "percentage_used": ("percentage_used_percent", "percent"),
        "media_errors": ("media_errors", "count"),
        "power_on_hours": ("power_on_hours", "hours"),
        "unsafe_shutdowns": ("unsafe_shutdowns", "count"),
        "error_log_entries": ("error_log_entries", "count"),
    }
    aggregate_modes = {
        "smart_passed": "min",
        "critical_warning": "max",
        "available_spare": "min",
        "percentage_used": "max",
        "media_errors": "sum",
        "power_on_hours": "max",
        "unsafe_shutdowns": "sum",
        "error_log_entries": "sum",
    }
    aggregate_values: dict[str, float] = {}
    metrics: list[dict[str, Any]] = []
    recorded_names: set[str] = set()
    temperatures: list[float] = []

    for index, device in enumerate(devices):
        if not isinstance(device, dict):
            continue
        device_path = str(device.get("name") or "").strip()
        if not device_path:
            continue
        command = ["-a", "--json"]
        device_type = str(device.get("type") or "").strip()
        if device_type:
            command.extend(["-d", device_type])
        command.append(device_path)
        payload = _smartctl_json(command, command_runner)
        if not payload:
            continue

        protocol = " ".join(
            str(value or "")
            for value in (
                device.get("protocol"),
                device.get("type"),
                payload.get("device", {}).get("protocol") if isinstance(payload.get("device"), dict) else None,
            )
        ).lower()
        health_log = payload.get("nvme_smart_health_information_log")
        if "nvme" not in protocol and not isinstance(health_log, dict):
            continue
        health_log = health_log if isinstance(health_log, dict) else {}

        label = str(payload.get("model_name") or device.get("info_name") or Path(device_path).name)
        device_name = _safe_metric_part(label)
        if device_name in recorded_names:
            device_name = f"{device_name}_{index}"
        recorded_names.add(device_name)

        smart_status = payload.get("smart_status")
        passed = smart_status.get("passed") if isinstance(smart_status, dict) else None
        values: dict[str, float] = {}
        if isinstance(passed, bool):
            values["smart_passed"] = 1.0 if passed else 0.0

        for value_name in (
            "critical_warning",
            "available_spare",
            "percentage_used",
            "media_errors",
            "power_on_hours",
            "unsafe_shutdowns",
        ):
            value = _coerce_metric_number(health_log.get(value_name))
            if value is not None and value >= 0:
                values[value_name] = value
        error_entries = _coerce_metric_number(health_log.get("num_err_log_entries"))
        if error_entries is not None and error_entries >= 0:
            values["error_log_entries"] = error_entries

        temperature = _nested_metric_number(payload, "temperature", "current")
        if temperature is None:
            temperature = _coerce_metric_number(health_log.get("temperature"))
        if temperature is not None and 0 < temperature < 150:
            temperatures.append(temperature)
            metrics.append(_metric(f"nvme.{device_name}.temp_c", temperature, "celsius", observed_at))

        for value_name, value in values.items():
            suffix, unit = metric_specs[value_name]
            metrics.append(_metric(f"nvme.{device_name}.{suffix}", value, unit, observed_at))
            current = aggregate_values.get(value_name)
            mode = aggregate_modes[value_name]
            if current is None:
                aggregate_values[value_name] = value
            elif mode == "min":
                aggregate_values[value_name] = min(current, value)
            elif mode == "max":
                aggregate_values[value_name] = max(current, value)
            else:
                aggregate_values[value_name] = current + value

    if temperatures:
        metrics.insert(0, _metric("nvme.temp_c", max(temperatures), "celsius", observed_at))
    for value_name, value in aggregate_values.items():
        suffix, unit = metric_specs[value_name]
        metrics.insert(0, _metric(f"nvme.{suffix}", value, unit, observed_at))
    return metrics


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


def _windows_processor_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-CimInstance Win32_Processor | "
        "Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress",
        command_runner,
    )
    physical_cores = 0.0
    logical_threads = 0.0
    for processor in _json_items(payload):
        cores = processor.get("NumberOfCores")
        threads = processor.get("NumberOfLogicalProcessors")
        if isinstance(cores, (int, float)):
            physical_cores += float(cores)
        if isinstance(threads, (int, float)):
            logical_threads += float(threads)

    metrics: list[dict[str, Any]] = []
    if physical_cores > 0:
        metrics.append(_metric("cpu.physical_cores", physical_cores, "count", observed_at))
    if logical_threads > 0:
        metrics.append(_metric("cpu.logical_threads", logical_threads, "count", observed_at))
    return metrics


def _windows_memory_metric(observed_at: str, command_runner: CommandRunner | None) -> dict[str, Any] | None:
    payload = _powershell_json(
        "Get-CimInstance Win32_OperatingSystem | "
        "Select-Object TotalVisibleMemorySize,FreePhysicalMemory | ConvertTo-Json -Compress",
        command_runner,
    )
    items = _json_items(payload)
    if not items:
        return None
    total = items[0].get("TotalVisibleMemorySize")
    free = items[0].get("FreePhysicalMemory")
    if not isinstance(total, (int, float)) or not isinstance(free, (int, float)) or total <= 0:
        return None
    return _metric("memory.used_percent", ((float(total) - float(free)) / float(total)) * 100, "percent", observed_at)


def _windows_battery_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-CimInstance Win32_Battery | "
        "Select-Object EstimatedChargeRemaining,BatteryStatus | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics: list[dict[str, Any]] = []
    for battery in _json_items(payload)[:1]:
        charge = battery.get("EstimatedChargeRemaining")
        if isinstance(charge, (int, float)) and 0 <= charge <= 100:
            metrics.append(_metric("battery.capacity_percent", float(charge), "percent", observed_at))
        status = battery.get("BatteryStatus")
        if isinstance(status, (int, float)):
            metrics.append(_metric("battery.ac_online", 0.0 if int(status) == 1 else 1.0, "boolean", observed_at))
    return metrics


def _network_speed_mbps(value: str) -> float | None:
    match = re.search(r"([0-9.]+)\s*([GMK]?)\s*(?:b(?:it)?/s|bps)", value, flags=re.IGNORECASE)
    if not match:
        return None
    return _wifi_bitrate_value_mbps(match.group(1), f"{match.group(2)}bit/s")


def _windows_netsh_outputs(command_runner: CommandRunner | None) -> list[str]:
    commands = [
        ["netsh", "wlan", "show", "interfaces"],
        [r"C:\Windows\System32\netsh.exe", "wlan", "show", "interfaces"],
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "$netsh=Join-Path $env:SystemRoot 'System32\\netsh.exe'; & $netsh wlan show interfaces | Out-String",
        ],
    ]
    outputs: list[str] = []
    seen: set[str] = set()
    for command in commands:
        output = _run_observation_command(command, command_runner, timeout=15.0)
        if output and output not in seen:
            outputs.append(output)
            seen.add(output)
        if outputs and command_runner is not None:
            break
    return outputs


def _windows_metrics_from_netsh_output(output: str, observed_at: str) -> list[dict[str, Any]]:
    if not output:
        return []

    sections: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        normalized_key = _safe_metric_part(key)
        if normalized_key == "name" and current:
            sections.append(current)
            current = []
        current.append((key, value))
    if current:
        sections.append(current)

    metrics: list[dict[str, Any]] = []
    generic_signal_recorded = False
    generic_bitrates_recorded: set[str] = set()
    for index, section in enumerate(sections):
        section_values: dict[str, str] = {}
        unnamed_bitrates: list[float] = []
        interface = f"wifi{index}"
        signal_percent: float | None = None
        for raw_key, value in section:
            normalized_key = _safe_metric_part(raw_key)
            section_values[normalized_key] = value
            if normalized_key == "name" and value:
                parsed_interface = _safe_metric_part(value)
                interface = parsed_interface if parsed_interface != "unknown" else f"wifi{index}"
            parsed = _parse_metric_number(value)
            if normalized_key == "signal" or (value.strip().endswith("%") and parsed is not None and 0 <= parsed <= 100):
                signal_percent = parsed
            if "mbps" in raw_key.lower() and parsed is not None:
                unnamed_bitrates.append(parsed)

        if signal_percent is not None:
            # Windows netsh exposes signal quality as percent. Approximate dBm
            # so the existing Wi-Fi signal UI can classify it.
            signal_dbm = (signal_percent / 2.0) - 100.0
            if not generic_signal_recorded:
                metrics.append(_metric("wifi.signal_dbm", signal_dbm, "dbm", observed_at))
                generic_signal_recorded = True
            metrics.append(_metric(f"wifi.{interface}.signal_dbm", signal_dbm, "dbm", observed_at))

        rx_value = _parse_metric_number(section_values.get("receive_rate_mbps", ""))
        tx_value = _parse_metric_number(section_values.get("transmit_rate_mbps", ""))
        if rx_value is None and unnamed_bitrates:
            rx_value = unnamed_bitrates[0]
        if tx_value is None and len(unnamed_bitrates) > 1:
            tx_value = unnamed_bitrates[1]

        for value, metric_suffix, generic_name in (
            (rx_value, "rx_bitrate_mbps", "wifi.rx_bitrate_mbps"),
            (tx_value, "tx_bitrate_mbps", "wifi.tx_bitrate_mbps"),
        ):
            if value is None:
                continue
            metrics.append(_metric(f"wifi.{interface}.{metric_suffix}", value, "mbps", observed_at))
            if generic_name not in generic_bitrates_recorded:
                metrics.append(_metric(generic_name, value, "mbps", observed_at))
                generic_bitrates_recorded.add(generic_name)
    return metrics


def _windows_netsh_wifi_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    metrics_by_name: dict[str, dict[str, Any]] = {}
    for output in _windows_netsh_outputs(command_runner):
        for metric in _windows_metrics_from_netsh_output(output, observed_at):
            metrics_by_name.setdefault(metric["name"], metric)
    return list(metrics_by_name.values())


def _windows_wmi_wifi_signal_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-CimInstance -Namespace root/wmi -ClassName MSNdis_80211_ReceivedSignalStrength -ErrorAction SilentlyContinue | "
        "Select-Object InstanceName,Ndis80211ReceivedSignalStrength | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics: list[dict[str, Any]] = []
    generic_recorded = False
    for index, item in enumerate(_json_items(payload)):
        raw_signal = item.get("Ndis80211ReceivedSignalStrength")
        if not isinstance(raw_signal, (int, float)):
            continue
        signal = float(raw_signal)
        if 0 <= signal <= 100:
            signal = (signal / 2.0) - 100.0
        if not -120 <= signal <= 0:
            continue
        interface = _safe_metric_part(str(item.get("InstanceName") or f"wifi{index}"))
        if interface == "unknown":
            interface = f"wifi{index}"
        if not generic_recorded:
            metrics.append(_metric("wifi.signal_dbm", signal, "dbm", observed_at))
            generic_recorded = True
        metrics.append(_metric(f"wifi.{interface}.signal_dbm", signal, "dbm", observed_at))
    return metrics


def _windows_adapter_wifi_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-NetAdapter -Physical | "
        "Select-Object Name,InterfaceDescription,Status,LinkSpeed,NdisPhysicalMedium | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics: list[dict[str, Any]] = []
    generic_recorded = False
    for index, adapter in enumerate(_json_items(payload)):
        status = str(adapter.get("Status") or "").lower()
        if status and status != "up":
            continue
        descriptor = " ".join(
            str(adapter.get(key) or "")
            for key in ("Name", "InterfaceDescription", "NdisPhysicalMedium")
        ).lower()
        ndis_physical_medium = adapter.get("NdisPhysicalMedium")
        is_wifi_medium = isinstance(ndis_physical_medium, (int, float)) and int(ndis_physical_medium) in {9, 10}
        if not is_wifi_medium and not any(
            marker in descriptor for marker in ("wi-fi", "wifi", "wireless", "wlan", "802.11", "802_11")
        ):
            continue
        raw_interface = str(adapter.get("Name") or adapter.get("InterfaceDescription") or f"wifi{index}")
        interface = _safe_metric_part(raw_interface)
        if interface == "unknown":
            interface = f"wifi{index}"
        link_speed = adapter.get("LinkSpeed")
        if not isinstance(link_speed, str):
            continue
        value = _network_speed_mbps(link_speed)
        if value is None:
            continue
        metrics.append(_metric(f"wifi.{interface}.link_bitrate_mbps", value, "mbps", observed_at))
        if not generic_recorded:
            metrics.append(_metric("wifi.link_bitrate_mbps", value, "mbps", observed_at))
            generic_recorded = True
    return metrics


def _windows_wifi_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    netsh_metrics = _windows_netsh_wifi_metrics(observed_at, command_runner)
    wmi_signal_metrics = _windows_wmi_wifi_signal_metrics(observed_at, command_runner)
    adapter_metrics = _windows_adapter_wifi_metrics(observed_at, command_runner)
    by_name = {metric["name"]: metric for metric in adapter_metrics}
    by_name.update({metric["name"]: metric for metric in wmi_signal_metrics})
    by_name.update({metric["name"]: metric for metric in netsh_metrics})
    return list(by_name.values())


def _windows_disk_is_nvme(disk: dict[str, Any]) -> bool:
    descriptor = " ".join(
        str(disk.get(key) or "")
        for key in ("Model", "FriendlyName", "InterfaceType", "BusType", "MediaType", "Description")
    ).lower()
    bus_type = _coerce_metric_number(disk.get("BusType"))
    return "nvme" in descriptor or bus_type == 17


def _windows_disk_device_name(disk: dict[str, Any], fallback_index: int) -> str:
    label_source = str(
        disk.get("Model")
        or disk.get("FriendlyName")
        or disk.get("DeviceId")
        or disk.get("Index")
        or f"nvme{fallback_index}"
    )
    device_name = _safe_metric_part(label_source)
    return device_name if device_name != "unknown" else f"nvme{fallback_index}"


def _windows_nvme_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payloads = [
        _powershell_json(
            "Get-CimInstance Win32_DiskDrive | "
            "Select-Object Index,Model,InterfaceType,MediaType,Size | ConvertTo-Json -Compress",
            command_runner,
        ),
        _powershell_json(
            "Get-PhysicalDisk | "
            "Select-Object DeviceId,FriendlyName,BusType,MediaType,Size | ConvertTo-Json -Compress",
            command_runner,
        ),
    ]
    metrics: list[dict[str, Any]] = []
    total_capacity = 0.0
    recorded_devices: set[str] = set()
    for payload in payloads:
        for index, disk in enumerate(_json_items(payload)):
            if not _windows_disk_is_nvme(disk):
                continue
            size = _coerce_metric_number(disk.get("Size"))
            if size is None or size <= 0:
                continue
            device_name = _windows_disk_device_name(disk, index)
            if device_name in recorded_devices:
                continue
            recorded_devices.add(device_name)
            capacity_bytes = float(size)
            total_capacity += capacity_bytes
            metrics.append(_metric(f"nvme.{device_name}.capacity_bytes", capacity_bytes, "bytes", observed_at))
    if total_capacity > 0:
        metrics.insert(0, _metric("nvme.capacity_bytes", total_capacity, "bytes", observed_at))
    metrics.extend(_windows_nvme_reliability_metrics(observed_at, command_runner))
    metrics.extend(_windows_nvme_io_metrics(observed_at, command_runner))
    return metrics


def _windows_nvme_io_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "$physical=@{};"
        "Get-PhysicalDisk -ErrorAction SilentlyContinue | ForEach-Object { $physical[[string]$_.DeviceId]=$_ };"
        "Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk -ErrorAction SilentlyContinue | "
        "Where-Object {$_.Name -ne '_Total'} | ForEach-Object {"
        "$name=[string]$_.Name;"
        "$diskId=$name;"
        "if ($name -match '^\\d+') { $diskId=$Matches[0] };"
        "$disk=$physical[$diskId];"
        "[pscustomobject]@{DeviceId=$diskId;Name=$name;FriendlyName=$disk.FriendlyName;"
        "BusType=$disk.BusType;MediaType=$disk.MediaType;"
        "DiskReadBytesPersec=$_.DiskReadBytesPersec;DiskWriteBytesPersec=$_.DiskWriteBytesPersec}"
        "} | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics: list[dict[str, Any]] = []
    total_read_bps = 0.0
    total_write_bps = 0.0
    read_samples = 0
    write_samples = 0
    recorded_devices: set[str] = set()
    for index, disk in enumerate(_json_items(payload)):
        if not _windows_disk_is_nvme(disk):
            continue
        device_name = _windows_disk_device_name(disk, index)
        if device_name in recorded_devices:
            continue
        recorded_devices.add(device_name)
        read_bps = _coerce_metric_number(disk.get("DiskReadBytesPersec"))
        write_bps = _coerce_metric_number(disk.get("DiskWriteBytesPersec"))
        if read_bps is not None and read_bps >= 0:
            metrics.append(_metric(f"nvme.{device_name}.read_bytes_per_sec", read_bps, "bytes_per_sec", observed_at))
            total_read_bps += read_bps
            read_samples += 1
        if write_bps is not None and write_bps >= 0:
            metrics.append(_metric(f"nvme.{device_name}.write_bytes_per_sec", write_bps, "bytes_per_sec", observed_at))
            total_write_bps += write_bps
            write_samples += 1
    if write_samples:
        metrics.insert(0, _metric("nvme.write_bytes_per_sec", total_write_bps, "bytes_per_sec", observed_at))
    if read_samples:
        metrics.insert(0, _metric("nvme.read_bytes_per_sec", total_read_bps, "bytes_per_sec", observed_at))
    return metrics


def _windows_nvme_reliability_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "$hasReliability=Get-Command Get-StorageReliabilityCounter -ErrorAction SilentlyContinue;"
        "Get-PhysicalDisk | ForEach-Object {"
        "$disk=$_;"
        "$counter=$null;"
        "if ($hasReliability) { $counter=$disk | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue };"
        "[pscustomobject]@{DeviceId=$disk.DeviceId;FriendlyName=$disk.FriendlyName;"
        "BusType=$disk.BusType;MediaType=$disk.MediaType;Size=$disk.Size;"
        "HealthStatus=[string]$disk.HealthStatus;OperationalStatus=[string]$disk.OperationalStatus;"
        "Temperature=$counter.Temperature;Wear=$counter.Wear;PowerOnHours=$counter.PowerOnHours;"
        "ReadErrorsUncorrected=$counter.ReadErrorsUncorrected;"
        "WriteErrorsUncorrected=$counter.WriteErrorsUncorrected}"
        "} | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics: list[dict[str, Any]] = []
    recorded_devices: set[str] = set()
    temperatures: list[float] = []
    smart_passed_values: list[float] = []
    wear_values: list[float] = []
    power_on_hours_values: list[float] = []
    media_errors_total = 0.0
    media_error_samples = 0
    for index, disk in enumerate(_json_items(payload)):
        if not _windows_disk_is_nvme(disk):
            continue
        device_name = _windows_disk_device_name(disk, index)
        if device_name in recorded_devices:
            continue
        recorded_devices.add(device_name)

        celsius = _coerce_metric_number(disk.get("Temperature"))
        if celsius is not None and 0 < celsius < 150:
            temperatures.append(celsius)
            metrics.append(_metric(f"nvme.{device_name}.temp_c", celsius, "celsius", observed_at))

        health_status = str(disk.get("HealthStatus") or "").strip().lower()
        operational_status = str(disk.get("OperationalStatus") or "").strip().lower()
        if health_status:
            passed = 1.0 if health_status == "healthy" and operational_status in {"", "ok"} else 0.0
            smart_passed_values.append(passed)
            metrics.append(_metric(f"nvme.{device_name}.smart_passed", passed, "boolean", observed_at))

        wear = _coerce_metric_number(disk.get("Wear"))
        if wear is not None and 0 <= wear <= 100:
            wear_values.append(wear)
            metrics.append(_metric(f"nvme.{device_name}.percentage_used_percent", wear, "percent", observed_at))

        power_on_hours = _coerce_metric_number(disk.get("PowerOnHours"))
        if power_on_hours is not None and power_on_hours >= 0:
            power_on_hours_values.append(power_on_hours)
            metrics.append(_metric(f"nvme.{device_name}.power_on_hours", power_on_hours, "hours", observed_at))

        read_errors = _coerce_metric_number(disk.get("ReadErrorsUncorrected"))
        write_errors = _coerce_metric_number(disk.get("WriteErrorsUncorrected"))
        if read_errors is not None or write_errors is not None:
            media_errors = max(0.0, read_errors or 0.0) + max(0.0, write_errors or 0.0)
            media_errors_total += media_errors
            media_error_samples += 1
            metrics.append(_metric(f"nvme.{device_name}.media_errors", media_errors, "count", observed_at))

    if temperatures:
        metrics.insert(0, _metric("nvme.temp_c", max(temperatures), "celsius", observed_at))
    if smart_passed_values:
        metrics.insert(0, _metric("nvme.smart_passed", min(smart_passed_values), "boolean", observed_at))
    if wear_values:
        metrics.insert(0, _metric("nvme.percentage_used_percent", max(wear_values), "percent", observed_at))
    if power_on_hours_values:
        metrics.insert(0, _metric("nvme.power_on_hours", max(power_on_hours_values), "hours", observed_at))
    if media_error_samples:
        metrics.insert(0, _metric("nvme.media_errors", media_errors_total, "count", observed_at))
    return metrics


def _windows_thermal_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-CimInstance -Namespace root/wmi MSAcpi_ThermalZoneTemperature | "
        "Select-Object CurrentTemperature | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics: list[dict[str, Any]] = []
    for index, sensor in enumerate(_json_items(payload)):
        raw_temperature = sensor.get("CurrentTemperature")
        if not isinstance(raw_temperature, (int, float)):
            continue
        celsius = (float(raw_temperature) / 10.0) - 273.15
        if 0 < celsius < 150:
            metrics.append(_metric(f"thermal.windows_zone_{index}.temp_c", celsius, "celsius", observed_at))
    metrics.extend(_windows_performance_thermal_metrics(observed_at, command_runner))
    metrics.extend(_windows_temperature_probe_metrics(observed_at, command_runner))
    metrics.extend(_windows_hardware_monitor_temperature_metrics(observed_at, command_runner))
    return metrics


def _windows_performance_thermal_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation "
        "-ErrorAction SilentlyContinue | "
        "Select-Object Name,Temperature,HighPrecisionTemperature | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics_by_name: dict[str, dict[str, Any]] = {}
    for index, sensor in enumerate(_json_items(payload)):
        high_precision = _coerce_metric_number(sensor.get("HighPrecisionTemperature"))
        kelvin = high_precision / 10.0 if high_precision is not None and high_precision > 1000 else None
        if kelvin is None:
            temperature = _coerce_metric_number(sensor.get("Temperature"))
            kelvin = temperature if temperature is not None and temperature > 200 else None
        if kelvin is None:
            continue
        celsius = kelvin - 273.15
        if not 0 < celsius < 150:
            continue
        sensor_name = _safe_metric_part(str(sensor.get("Name") or f"zone_{index}"))
        metric_name = f"thermal.windows_zone_{sensor_name}.temp_c"
        metrics_by_name.setdefault(metric_name, _metric(metric_name, celsius, "celsius", observed_at))
    return list(metrics_by_name.values())


def _windows_temperature_probe_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "Get-CimInstance Win32_TemperatureProbe -ErrorAction SilentlyContinue | "
        "Select-Object Name,DeviceID,CurrentReading | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics_by_name: dict[str, dict[str, Any]] = {}
    for index, probe in enumerate(_json_items(payload)):
        raw_value = _coerce_metric_number(probe.get("CurrentReading"))
        if raw_value is None:
            continue
        celsius = (raw_value / 10.0) - 273.15 if raw_value > 1000 else raw_value
        if not 0 < celsius < 150:
            continue
        label = " ".join(str(probe.get(key) or "") for key in ("Name", "DeviceID")).strip()
        normalized_label = label.lower()
        if "cpu" in normalized_label and any(token in normalized_label for token in ("package", "tctl", "tdie")):
            metric_name = "cpu.package_temp_c"
        else:
            core_match = re.search(r"\bcore\s*#?\s*(\d+)\b", normalized_label)
            if "cpu" in normalized_label and core_match:
                metric_name = f"cpu.core_{core_match.group(1)}.temp_c"
            else:
                sensor_name = _safe_metric_part(label or f"temperature_probe_{index}")
                metric_name = f"thermal.windows_probe_{sensor_name}.temp_c"
        metrics_by_name.setdefault(metric_name, _metric(metric_name, celsius, "celsius", observed_at))
    return list(metrics_by_name.values())


def _windows_cpu_core_sensor_metric_name(sensor_name: str, suffix: str) -> str | None:
    lower_name = sensor_name.lower()
    hybrid_match = re.search(r"\b(lp[-\s]?e|p|e)[-\s]?core\s*#?\s*(\d+)\b", lower_name)
    if hybrid_match:
        raw_group = hybrid_match.group(1).replace("-", "").replace(" ", "")
        group = "lp_e" if raw_group == "lpe" else raw_group
        return f"cpu.{group}_core_{hybrid_match.group(2)}.{suffix}"
    core_match = re.search(r"\b(?:cpu\s+)?core\s*#?\s*(\d+)\b", lower_name)
    if core_match:
        return f"cpu.core_{core_match.group(1)}.{suffix}"
    return None


def _windows_cpu_load_metric_name(sensor_name: str) -> str | None:
    lower_name = sensor_name.lower()
    if any(token in lower_name for token in ("total", "package", "cpu total")):
        return "cpu.load_percent"
    return _windows_cpu_core_sensor_metric_name(sensor_name, "load_percent")


def _windows_hardware_monitor_temperature_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    namespaces = ("root/LibreHardwareMonitor", "root/OpenHardwareMonitor")
    metrics_by_name: dict[str, dict[str, Any]] = {}
    nvme_generic_recorded = False
    for namespace in namespaces:
        payload = _powershell_json(
            f"Get-CimInstance -Namespace {namespace} -ClassName Sensor -ErrorAction SilentlyContinue | "
            "Where-Object {$_.SensorType -eq 'Temperature'} | "
            "Select-Object Name,Parent,Value | ConvertTo-Json -Compress",
            command_runner,
        )
        for index, sensor in enumerate(_json_items(payload)):
            raw_value = sensor.get("Value")
            if not isinstance(raw_value, (int, float)):
                continue
            celsius = float(raw_value)
            if not 0 < celsius < 150:
                continue
            label = " ".join(str(sensor.get(key) or "") for key in ("Parent", "Name")).strip()
            normalized_label = label.lower()
            name = str(sensor.get("Name") or f"temperature_{index}")
            if "cpu" in normalized_label and any(token in normalized_label for token in ("package", "tctl", "tdie")):
                metric_name = "cpu.package_temp_c"
            else:
                cpu_core_metric = _windows_cpu_core_sensor_metric_name(name, "temp_c")
                if ("cpu" in normalized_label or "core" in normalized_label) and cpu_core_metric:
                    metric_name = cpu_core_metric
                elif any(token in normalized_label for token in ("nvme", "ssd", "disk")):
                    device_name = _safe_metric_part(label or name)
                    metric_name = f"nvme.{device_name}.temp_c"
                    if not nvme_generic_recorded:
                        metrics_by_name.setdefault("nvme.temp_c", _metric("nvme.temp_c", celsius, "celsius", observed_at))
                        nvme_generic_recorded = True
                else:
                    metric_name = f"thermal.windows_{_safe_metric_part(label or name)}.temp_c"
            metrics_by_name.setdefault(metric_name, _metric(metric_name, celsius, "celsius", observed_at))
        if metrics_by_name:
            break
    return list(metrics_by_name.values())


def _windows_hardware_monitor_load_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    namespaces = ("root/LibreHardwareMonitor", "root/OpenHardwareMonitor")
    metrics_by_name: dict[str, dict[str, Any]] = {}
    core_loads: list[float] = []
    for namespace in namespaces:
        payload = _powershell_json(
            f"Get-CimInstance -Namespace {namespace} -ClassName Sensor -ErrorAction SilentlyContinue | "
            "Where-Object {$_.SensorType -eq 'Load'} | "
            "Select-Object Name,Parent,Value | ConvertTo-Json -Compress",
            command_runner,
        )
        for sensor in _json_items(payload):
            value = _coerce_metric_number(sensor.get("Value"))
            if value is None or not 0 <= value <= 100:
                continue
            label = " ".join(str(sensor.get(key) or "") for key in ("Parent", "Name")).strip()
            normalized_label = label.lower()
            name = str(sensor.get("Name") or "")
            if not any(token in normalized_label for token in ("cpu", "intel", "amd", "core")):
                continue
            metric_name = _windows_cpu_load_metric_name(name)
            if metric_name is None:
                continue
            if metric_name != "cpu.load_percent":
                core_loads.append(value)
            metrics_by_name.setdefault(metric_name, _metric(metric_name, value, "percent", observed_at))
        if metrics_by_name:
            break
    if "cpu.load_percent" not in metrics_by_name and core_loads:
        metrics_by_name["cpu.load_percent"] = _metric("cpu.load_percent", max(core_loads), "percent", observed_at)
    return list(metrics_by_name.values())


def _windows_native_fan_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "$items=@();"
        "$items += Get-CimInstance Win32_Fan -ErrorAction SilentlyContinue | "
        "Select-Object Name,DeviceID,CurrentReading,DesiredSpeed;"
        "$items += Get-CimInstance Win32_Tachometer -ErrorAction SilentlyContinue | "
        "Select-Object Name,DeviceID,CurrentReading,DesiredSpeed;"
        "$items | ConvertTo-Json -Compress",
        command_runner,
    )
    metrics_by_name: dict[str, dict[str, Any]] = {}
    generic_recorded = False
    for index, fan in enumerate(_json_items(payload)):
        rpm = _coerce_metric_number(fan.get("CurrentReading"))
        if rpm is None or rpm <= 0:
            rpm = _coerce_metric_number(fan.get("DesiredSpeed"))
        if rpm is None or not 0 <= rpm < 50000:
            continue
        label = " ".join(str(fan.get(key) or "") for key in ("Name", "DeviceID")).strip()
        device_name = _safe_metric_part(label or f"fan{index}")
        if device_name == "unknown":
            device_name = f"fan{index}"
        if not generic_recorded:
            metrics_by_name.setdefault("fan.rpm", _metric("fan.rpm", rpm, "rpm", observed_at))
            generic_recorded = True
        metric_name = f"fan.{device_name}.rpm"
        metrics_by_name.setdefault(metric_name, _metric(metric_name, rpm, "rpm", observed_at))
    return list(metrics_by_name.values())


def _windows_hardware_monitor_fan_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    namespaces = ("root/LibreHardwareMonitor", "root/OpenHardwareMonitor")
    metrics_by_name: dict[str, dict[str, Any]] = {}
    generic_recorded = False
    for namespace in namespaces:
        payload = _powershell_json(
            f"Get-CimInstance -Namespace {namespace} -ClassName Sensor -ErrorAction SilentlyContinue | "
            "Where-Object {$_.SensorType -eq 'Fan'} | "
            "Select-Object Name,Parent,Value | ConvertTo-Json -Compress",
            command_runner,
        )
        for index, sensor in enumerate(_json_items(payload)):
            rpm = _coerce_metric_number(sensor.get("Value"))
            if rpm is None or not 0 <= rpm < 50000:
                continue
            label = " ".join(str(sensor.get(key) or "") for key in ("Parent", "Name")).strip()
            device_name = _safe_metric_part(label or str(sensor.get("Name") or f"fan{index}"))
            if device_name == "unknown":
                device_name = f"fan{index}"
            metric_name = f"fan.{device_name}.rpm"
            if not generic_recorded:
                metrics_by_name.setdefault("fan.rpm", _metric("fan.rpm", rpm, "rpm", observed_at))
                generic_recorded = True
            metrics_by_name.setdefault(metric_name, _metric(metric_name, rpm, "rpm", observed_at))
        if metrics_by_name:
            break
    return list(metrics_by_name.values())


def _windows_hardware_monitor_library_metrics(
    observed_at: str,
    command_runner: CommandRunner | None,
) -> list[dict[str, Any]]:
    payload = _powershell_json(
        "$dll=$env:QUIPU_LIBRE_HARDWARE_MONITOR_DLL;"
        "$process=Get-Process LibreHardwareMonitor -ErrorAction SilentlyContinue | Select-Object -First 1;"
        "if (-not $dll -and $process -and $process.Path) {"
        "$candidate=Join-Path (Split-Path $process.Path) 'LibreHardwareMonitorLib.dll';"
        "if (Test-Path -LiteralPath $candidate) { $dll=$candidate }"
        "};"
        "if (-not $dll) {"
        "$command=Get-Command LibreHardwareMonitor.exe -ErrorAction SilentlyContinue;"
        "if ($command) { $dll=Join-Path (Split-Path $command.Source) 'LibreHardwareMonitorLib.dll' }"
        "};"
        "if (-not $dll) {"
        "$roots=@($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA) | Where-Object { $_ };"
        "$dll=$roots | ForEach-Object {"
        "Get-ChildItem $_ -Directory -Filter 'LibreHardwareMonitor*' -ErrorAction SilentlyContinue"
        "} | ForEach-Object {"
        "Get-ChildItem $_.FullName -File -Recurse -Filter 'LibreHardwareMonitorLib.dll' -ErrorAction SilentlyContinue"
        "} | Select-Object -First 1 -ExpandProperty FullName"
        "};"
        "if (-not $dll -and $env:LOCALAPPDATA) {"
        "$packages=Join-Path $env:LOCALAPPDATA 'Microsoft\\WinGet\\Packages';"
        "$dll=Get-ChildItem $packages -Directory -Filter 'LibreHardwareMonitor.LibreHardwareMonitor*' "
        "-ErrorAction SilentlyContinue | ForEach-Object {"
        "Get-ChildItem $_.FullName -File -Recurse -Filter 'LibreHardwareMonitorLib.dll' -ErrorAction SilentlyContinue"
        "} | Select-Object -First 1 -ExpandProperty FullName"
        "};"
        "if (-not $dll -or -not (Test-Path -LiteralPath $dll)) { Write-Output '[]'; exit 0 };"
        "Add-Type -Path $dll;"
        "$computer=[LibreHardwareMonitor.Hardware.Computer]::new();"
        "$computer.IsCpuEnabled=$true;"
        "$computer.IsMotherboardEnabled=$true;"
        "$computer.IsStorageEnabled=$true;"
        "$computer.Open();"
        "function Update-Hardware($hardware) {"
        "$hardware.Update();"
        "foreach ($sub in $hardware.SubHardware) { Update-Hardware $sub }"
        "};"
        "function Read-Hardware($hardware) {"
        "foreach ($sensor in $hardware.Sensors) {"
        "if ($sensor.SensorType -in @('Temperature','Fan','Load') -and $null -ne $sensor.Value) {"
        "[pscustomobject]@{Hardware=$hardware.Name;HardwareType=[string]$hardware.HardwareType;"
        "Name=$sensor.Name;SensorType=[string]$sensor.SensorType;Value=[double]$sensor.Value;"
        "Identifier=[string]$sensor.Identifier}"
        "}"
        "};"
        "foreach ($sub in $hardware.SubHardware) { Read-Hardware $sub }"
        "};"
        "try {"
        "foreach ($hardware in $computer.Hardware) { Update-Hardware $hardware };"
        "Start-Sleep -Milliseconds 250;"
        "foreach ($hardware in $computer.Hardware) { Update-Hardware $hardware };"
        "@($computer.Hardware | ForEach-Object { Read-Hardware $_ }) | ConvertTo-Json -Compress"
        "} finally { $computer.Close() }",
        command_runner,
    )
    metrics_by_name: dict[str, dict[str, Any]] = {}
    nvme_temperatures: list[float] = []
    fan_values: list[float] = []
    core_loads: list[float] = []
    for index, sensor in enumerate(_json_items(payload)):
        value = _coerce_metric_number(sensor.get("Value"))
        if value is None:
            continue
        sensor_type = str(sensor.get("SensorType") or "").strip().lower()
        hardware_type = str(sensor.get("HardwareType") or "").strip().lower()
        hardware = str(sensor.get("Hardware") or "").strip()
        name = str(sensor.get("Name") or f"sensor_{index}").strip()
        label = " ".join(part for part in (hardware, name) if part).strip()
        normalized_label = label.lower()

        if sensor_type == "fan":
            if not 0 <= value < 50000:
                continue
            fan_values.append(value)
            metric_name = f"fan.{_safe_metric_part(label)}.rpm"
            metrics_by_name.setdefault(metric_name, _metric(metric_name, value, "rpm", observed_at))
            continue
        if sensor_type == "load":
            if not 0 <= value <= 100:
                continue
            if hardware_type == "cpu" or any(token in normalized_label for token in ("cpu", "intel", "amd", "core")):
                metric_name = _windows_cpu_load_metric_name(name)
                if metric_name is None:
                    continue
                if metric_name != "cpu.load_percent":
                    core_loads.append(value)
                metrics_by_name.setdefault(metric_name, _metric(metric_name, value, "percent", observed_at))
            continue
        if sensor_type != "temperature" or not 0 < value < 150:
            continue

        if hardware_type == "cpu" or "cpu" in normalized_label:
            lower_name = name.lower()
            if "package" in lower_name:
                metric_name = "cpu.package_temp_c"
            else:
                cpu_core_metric = _windows_cpu_core_sensor_metric_name(name, "temp_c")
                if cpu_core_metric:
                    metric_name = cpu_core_metric
                else:
                    metric_name = f"thermal.windows_{_safe_metric_part(label)}.temp_c"
        elif hardware_type == "storage" or any(
            token in normalized_label for token in ("nvme", "ssd", "disk")
        ):
            nvme_temperatures.append(value)
            metric_name = f"nvme.{_safe_metric_part(label)}.temp_c"
        else:
            metric_name = f"thermal.windows_{_safe_metric_part(label)}.temp_c"
        metrics_by_name.setdefault(metric_name, _metric(metric_name, value, "celsius", observed_at))

    if nvme_temperatures:
        metrics_by_name["nvme.temp_c"] = _metric(
            "nvme.temp_c", max(nvme_temperatures), "celsius", observed_at
        )
    if fan_values:
        metrics_by_name["fan.rpm"] = _metric("fan.rpm", max(fan_values), "rpm", observed_at)
    if "cpu.load_percent" not in metrics_by_name and core_loads:
        metrics_by_name["cpu.load_percent"] = _metric("cpu.load_percent", max(core_loads), "percent", observed_at)
    return list(metrics_by_name.values())


def _windows_metrics(observed_at: str, command_runner: CommandRunner | None) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    metrics.extend(_windows_processor_metrics(observed_at, command_runner))
    memory_metric = _windows_memory_metric(observed_at, command_runner)
    if memory_metric is not None:
        metrics.append(memory_metric)
    metrics.extend(_windows_battery_metrics(observed_at, command_runner))
    metrics.extend(_windows_wifi_metrics(observed_at, command_runner))
    metrics.extend(_windows_nvme_metrics(observed_at, command_runner))
    metrics.extend(_windows_thermal_metrics(observed_at, command_runner))
    metrics.extend(_windows_hardware_monitor_load_metrics(observed_at, command_runner))
    metrics.extend(_windows_native_fan_metrics(observed_at, command_runner))
    metrics.extend(_windows_hardware_monitor_fan_metrics(observed_at, command_runner))
    metrics.extend(_windows_hardware_monitor_library_metrics(observed_at, command_runner))
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
    windows_runtime = _is_windows_runtime(root_path)
    windows_device_info = _windows_device_info(command_runner) if windows_runtime else {}
    cpu_model = windows_device_info.get("cpu_model") if windows_runtime else None
    if not cpu_model:
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
    if windows_runtime:
        metrics.extend(_windows_metrics(observed_iso, command_runner))
    metrics.extend(_smartctl_metrics(observed_iso, command_runner))
    events = _event_logs(root_path, observed_iso, command_runner)
    if windows_runtime:
        events.extend(_windows_event_logs(observed_iso, command_runner))
        events = sorted({event["fingerprint"]: event for event in events}.values(), key=lambda event: event["observed_at"])[-20:]
    metrics = list({metric["name"]: metric for metric in metrics}.values())

    if not metrics and not events:
        raise RuntimeError("no readable system signals found")

    batch_seed = f"{collected_device_id}:{observed_iso}"
    batch_hash = hashlib.sha256(batch_seed.encode("utf-8")).hexdigest()[:12]
    return {
        "batch_id": f"collector-{batch_hash}",
        "observed_at": observed_iso,
        "device": {
            "device_id": collected_device_id,
            "display_name": device_alias.strip() if device_alias and device_alias.strip() else None,
            "hostname": _hostname(root_path),
            "model": windows_device_info.get("model") or _model(root_path),
            "cpu_model": cpu_model,
            "os_name": windows_device_info.get("os_name") or _os_name(root_path),
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
