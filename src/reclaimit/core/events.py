"""Typed events shared by workers and presentation layers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class EventKind(StrEnum):
    STATUS = "status"
    PROGRESS = "progress"
    WARNING = "warning"
    ERROR = "error"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class WorkerEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: EventKind
    message: str
    current: int = 0
    total: int = 0
    detail: str | None = None
