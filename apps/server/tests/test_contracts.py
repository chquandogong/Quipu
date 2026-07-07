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
