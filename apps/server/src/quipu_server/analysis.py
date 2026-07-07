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
