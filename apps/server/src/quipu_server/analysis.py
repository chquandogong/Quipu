from datetime import datetime, timezone
from typing import Any


RISK_ORDER = {"healthy": 0, "warning": 1, "critical": 2, "stale": 3}
PRIORITY_ORDER = {"High": 3, "Medium": 2, "Low": 1}


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


def _average_metric(samples: list[dict[str, Any]], name: str) -> float | None:
    values = [float(sample["value"]) for sample in samples if sample["name"] == name]
    if not values:
        return None
    return sum(values) / len(values)


def _format_celsius(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:.1f}C"


def _format_load(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:.2f}"


def _format_delta(value: float | None, unit: str) -> str | None:
    if value is None:
        return None
    if unit == "C":
        return f"{value:+.1f}C"
    if unit == "load":
        return f"{value:+.2f}"
    return f"{value:+.1f}"


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


def _priority_for_risk(risk_level: str) -> str:
    if risk_level == "critical":
        return "High"
    if risk_level in {"warning", "stale"}:
        return "Medium"
    return "Low"


def _next_step_for_category(category: str) -> str:
    return {
        "thermal": "Inspect thermal evidence and compare cooling or workload windows.",
        "graphics": "Inspect graphics/session timeline and repeated driver signatures.",
        "storage": "Check storage warnings, NVMe health, and I/O stall evidence.",
        "network": "Review reconnects, signal changes, and driver messages.",
        "update": "Compare package or kernel changes against the incident window.",
        "reboot": "Inspect pre-reboot graphics, thermal, storage, and power evidence.",
        "agent": "Confirm the device is online and the read-only collector is running.",
        "load": "Compare load and process context against thermal behavior.",
    }.get(category, "Inspect the evidence timeline and collect missing signals.")


def _action_for_category(category: str) -> dict[str, str]:
    actions = {
        "thermal": {
            "label": "Check cooling and workload",
            "description": "Record physical cooling changes and compare load-adjusted temperatures.",
        },
        "graphics": {
            "label": "Inspect graphics/session stack",
            "description": "Review kernel graphics warnings and session errors before changing drivers.",
        },
        "storage": {
            "label": "Check storage health",
            "description": "Review NVMe temperature, kernel storage messages, and SMART data if available.",
        },
        "network": {
            "label": "Check wireless stability",
            "description": "Compare reconnects, signal strength, and NetworkManager events.",
        },
        "update": {
            "label": "Correlate recent updates",
            "description": "Compare package, kernel, and firmware changes against the incident window.",
        },
        "reboot": {
            "label": "Reconstruct shutdown window",
            "description": "Inspect the last events before reboot or unclean shutdown markers.",
        },
        "agent": {
            "label": "Restore telemetry",
            "description": "Confirm the machine is online and the collector can send batches.",
        },
    }
    return actions.get(
        category,
        {
            "label": "Inspect evidence",
            "description": "Review the timeline and gather missing signals before acting.",
        },
    )


def _first_finding(device_view: dict[str, Any]) -> dict[str, str] | None:
    findings = device_view.get("findings", [])
    return findings[0] if findings else None


def _missing_metric_result(
    *,
    intervention: dict[str, Any],
    window_minutes: int,
    missing: str,
) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "summary": f"Need {missing} observations before Quipu can verify {intervention['label']}.",
        "window_minutes": window_minutes,
        "checks": [
            {
                "name": "CPU package temperature",
                "before": None,
                "after": None,
                "delta": None,
                "verdict": f"missing_{missing}",
            }
        ],
    }


def _build_intervention_verification(
    intervention: dict[str, Any],
    window: dict[str, Any] | None,
) -> dict[str, Any]:
    if not window:
        return {
            "status": "insufficient_data",
            "summary": f"Need before and after observations before Quipu can verify {intervention['label']}.",
            "window_minutes": 30,
            "checks": [
                {
                    "name": "CPU package temperature",
                    "before": None,
                    "after": None,
                    "delta": None,
                    "verdict": "missing_window",
                }
            ],
        }

    window_minutes = int(window["window_minutes"])
    before_metrics = window["metrics"]["before"]
    after_metrics = window["metrics"]["after"]
    before_temp = _average_metric(before_metrics, "cpu.package_temp_c")
    after_temp = _average_metric(after_metrics, "cpu.package_temp_c")
    if before_temp is None and after_temp is None:
        return _missing_metric_result(intervention=intervention, window_minutes=window_minutes, missing="before_and_after")
    if before_temp is None:
        return _missing_metric_result(intervention=intervention, window_minutes=window_minutes, missing="before")
    if after_temp is None:
        return _missing_metric_result(intervention=intervention, window_minutes=window_minutes, missing="after")

    temp_delta = after_temp - before_temp
    if temp_delta <= -5:
        temp_verdict = "improved"
    elif temp_delta >= 5:
        temp_verdict = "worsened"
    else:
        temp_verdict = "unchanged"

    checks: list[dict[str, Any]] = [
        {
            "name": "CPU package temperature",
            "before": _format_celsius(before_temp),
            "after": _format_celsius(after_temp),
            "delta": _format_delta(temp_delta, "C"),
            "verdict": temp_verdict,
        }
    ]

    before_load = _average_metric(before_metrics, "cpu.load_1m")
    after_load = _average_metric(after_metrics, "cpu.load_1m")
    load_note = "Load context was unavailable."
    if before_load is not None and after_load is not None:
        load_delta = after_load - before_load
        if abs(load_delta) <= 0.5:
            load_verdict = "similar"
            load_note = "Load was similar, so the temperature change is stronger cooling evidence."
        elif load_delta > 0.5:
            load_verdict = "higher"
            load_note = "Load was higher after the intervention, so a temperature drop is stronger cooling evidence."
        else:
            load_verdict = "lower"
            load_note = "Load was lower after the intervention, so part of the temperature drop may be workload-driven."
        checks.append(
            {
                "name": "1 minute load average",
                "before": _format_load(before_load),
                "after": _format_load(after_load),
                "delta": _format_delta(load_delta, "load"),
                "verdict": load_verdict,
            }
        )

    before_events = len(window["events"]["before"])
    after_events = len(window["events"]["after"])
    if after_events < before_events:
        event_verdict = "improved"
    elif after_events > before_events:
        event_verdict = "worsened"
    else:
        event_verdict = "unchanged"
    checks.append(
        {
            "name": "Warning recurrence",
            "before": str(before_events),
            "after": str(after_events),
            "delta": str(after_events - before_events),
            "verdict": event_verdict,
        }
    )

    verdicts = {check["verdict"] for check in checks}
    if "worsened" in verdicts:
        status = "worse"
        summary = f"Evidence worsened after {intervention['label']}; inspect the window before repeating the action."
    elif "improved" in verdicts:
        status = "helped"
        summary = (
            f"CPU package temperature fell by {abs(temp_delta):.1f}C after {intervention['label']}. "
            f"{load_note}"
        )
    else:
        status = "unclear"
        summary = f"Evidence changed too little to verify whether {intervention['label']} helped."

    return {
        "status": status,
        "summary": summary,
        "window_minutes": window_minutes,
        "checks": checks,
    }


def _verification_panel_from_result(result: dict[str, Any]) -> dict[str, Any]:
    status_labels = {
        "helped": "Helped",
        "worse": "Worse",
        "unclear": "Unclear",
        "insufficient_data": "Needs after data",
    }
    return {
        "status": status_labels.get(result["status"], "Waiting for after window"),
        "summary": result["summary"],
        "signals": [check["name"] for check in result["checks"]],
    }


def _queue_item(device_view: dict[str, Any], *, now: datetime) -> dict[str, Any] | None:
    finding = _first_finding(device_view)
    if not finding:
        return None

    device = device_view["device"]
    category = finding["category"]
    priority = _priority_for_risk(device_view["risk_level"])
    return {
        "id": f"{device['device_id']}:{category}",
        "priority": priority,
        "stage": "Triage",
        "risk_level": device_view["risk_level"],
        "device_id": device["device_id"],
        "device_hostname": device["hostname"],
        "title": finding["title"],
        "category": category,
        "confidence": finding["confidence"],
        "why_now": finding["title"],
        "evidence": finding["evidence"],
        "next_step": _next_step_for_category(category),
        "updated_at": now.isoformat(),
    }


def build_investigation_queue(
    snapshots: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    overview = build_fleet_overview(snapshots, now=now)
    generated_at = _parse_time(overview["generated_at"])
    items = [
        item
        for device_view in overview["devices"]
        if (item := _queue_item(device_view, now=generated_at)) is not None
    ]
    items.sort(key=lambda item: (-PRIORITY_ORDER[item["priority"]], item["device_hostname"]))
    return items


def build_investigation_detail(
    snapshots: list[dict[str, Any]],
    item_id: str,
    *,
    now: datetime | None = None,
    interventions: list[dict[str, Any]] | None = None,
    intervention_windows: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    queue = build_investigation_queue(snapshots, now=now)
    item = next((candidate for candidate in queue if candidate["id"] == item_id), None)
    if not item:
        return None

    overview = build_fleet_overview(snapshots, now=now)
    device_view = next(
        candidate for candidate in overview["devices"] if candidate["device"]["device_id"] == item["device_id"]
    )
    timeline = [
        {
            "observed_at": event["observed_at"],
            "category": event["category"],
            "severity": event["severity"],
            "source": event["source"],
            "summary": event["message_summary"],
            "raw_ref": event["raw_ref"],
        }
        for event in device_view["recent_events"]
    ]
    if not timeline:
        timeline = [
            {
                "observed_at": device_view["device"]["last_seen_at"],
                "category": item["category"],
                "severity": item["risk_level"],
                "source": "analysis",
                "summary": item["evidence"],
                "raw_ref": None,
            }
        ]

    intervention_windows = intervention_windows or {}
    recorded_interventions = [
        {
            **intervention,
            "verification_result": _build_intervention_verification(
                intervention,
                intervention_windows.get(intervention["id"]),
            ),
        }
        for intervention in (interventions or [])
    ]
    contradiction = (
        "An intervention is recorded; after-window evidence has not been compared yet."
        if recorded_interventions
        else "No before/after intervention window has been recorded yet."
    )
    hypothesis = {
        "category": item["category"],
        "title": item["title"],
        "confidence": item["confidence"],
        "supporting_evidence": [item["evidence"]],
        "contradicting_evidence": [contradiction],
        "missing_checks": [item["next_step"]],
    }
    action = _action_for_category(item["category"])
    if recorded_interventions:
        verification = _verification_panel_from_result(recorded_interventions[-1]["verification_result"])
    else:
        verification = {
            "status": "Needs before/after data",
            "summary": "Record an intervention and compare the next observation window.",
            "signals": ["temperature delta", "warning recurrence", "load context"],
        }
    return {
        "item": item,
        "timeline": timeline,
        "hypotheses": [hypothesis],
        "actions": [action],
        "interventions": recorded_interventions,
        "verification": verification,
        "report": {
            "summary": f"{item['device_hostname']} needs investigation for {item['category']} evidence.",
            "recommended_next_step": item["next_step"],
        },
        "fleet_context": {
            "device": device_view["device"],
            "latest_metrics": device_view["latest_metrics"],
            "recent_events": device_view["recent_events"],
        },
    }
