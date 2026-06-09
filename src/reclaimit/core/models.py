"""Domain models for devices, media catalogs, and sync plans."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    APP_DOCUMENT = "app_document"
    OTHER = "other"


class SyncDirection(StrEnum):
    DEVICE_TO_LOCAL = "device_to_local"
    LOCAL_TO_DEVICE = "local_to_device"
    BIDIRECTIONAL = "bidirectional"


class SyncAction(StrEnum):
    COPY_TO_SOURCE = "copy_to_source"
    COPY_TO_TARGET = "copy_to_target"
    DELETE_FROM_SOURCE = "delete_from_source"
    DELETE_FROM_TARGET = "delete_from_target"
    SKIP = "skip"
    CONFLICT = "conflict"


class ConflictPolicy(StrEnum):
    SKIP = "skip"
    OVERWRITE_LOCAL = "overwrite_local"
    OVERWRITE_DEVICE = "overwrite_device"
    COPY_AS_NEW = "copy_as_new"


class Device(BaseModel):
    model_config = ConfigDict(frozen=True)

    udid: str
    name: str | None = None
    product_type: str | None = None
    paired: bool = False
    trusted: bool = False


class MediaItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: PurePosixPath
    size: int
    modified_at: datetime | None = None
    checksum: str | None = None
    kind: MediaKind = MediaKind.OTHER
    deleted: bool = False

    @property
    def identity(self) -> str:
        return str(self.path)

    def content_signature(self) -> tuple[int, datetime | None, str | None]:
        return (self.size, self.modified_at, self.checksum)

    def same_content_as(self, other: "MediaItem") -> bool:
        if self.checksum and other.checksum:
            return self.checksum == other.checksum
        return self.size == other.size and self.modified_at == other.modified_at


class Catalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: tuple[MediaItem, ...] = Field(default_factory=tuple)

    @classmethod
    def from_items(cls, items: list[MediaItem] | tuple[MediaItem, ...]) -> "Catalog":
        return cls(items=tuple(items))

    def by_identity(self) -> dict[str, MediaItem]:
        return {item.identity: item for item in self.items}


class SyncPlanEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: SyncAction
    source: MediaItem | None = None
    target: MediaItem | None = None
    reason: str = ""
    destination_path: PurePosixPath | None = None


class SyncPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    direction: SyncDirection
    dry_run: bool
    entries: tuple[SyncPlanEntry, ...]

    @property
    def has_conflicts(self) -> bool:
        return any(entry.action == SyncAction.CONFLICT for entry in self.entries)

    @property
    def actionable_entries(self) -> tuple[SyncPlanEntry, ...]:
        return tuple(entry for entry in self.entries if entry.action != SyncAction.SKIP)
