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
