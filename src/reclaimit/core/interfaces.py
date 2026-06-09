"""Public interfaces shared across service and worker layers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import PurePosixPath
from typing import BinaryIO

from reclaimit.core.events import WorkerEvent
from reclaimit.core.models import Catalog, Device, MediaItem, SyncPlan


class DeviceClient(ABC):
    """Device operations exposed by the mobiledevice layer."""

    @abstractmethod
    def discover(self) -> list[Device]:
        """Return currently visible devices."""

    @abstractmethod
    def connect(self, udid: str) -> Device:
        """Connect to one device by UDID."""

    @abstractmethod
    def pair(self, udid: str) -> Device:
        """Run pairing/trust flow for one device."""

    @abstractmethod
    def disconnect(self, udid: str) -> None:
        """Release native resources for one device."""


class MediaProvider(ABC):
    """Common provider for photos, videos, music-like files, and app documents."""

    @abstractmethod
    def list_roots(self) -> list[PurePosixPath]:
        """Return browsable provider roots."""

    @abstractmethod
    def list_media_items(self, root: PurePosixPath | None = None) -> Catalog:
        """Return a catalog for one provider root or all roots."""

    @abstractmethod
    def open_read_stream(self, item: MediaItem) -> BinaryIO:
        """Open a readable stream for a media item."""

    @abstractmethod
    def open_write_stream(self, item: MediaItem) -> BinaryIO:
        """Open a writable stream for a media item."""

    def delete(self, item: MediaItem) -> None:
        raise NotImplementedError("delete is not supported by this provider")

    def move(self, item: MediaItem, destination: PurePosixPath) -> MediaItem:
        raise NotImplementedError("move is not supported by this provider")


class TransferExecutor(ABC):
    """Execute sync plans and emit progress events."""

    @abstractmethod
    def execute(self, plan: SyncPlan) -> Iterator[WorkerEvent]:
        """Execute a plan and yield typed worker events."""


class CatalogStore(ABC):
    """Persistent catalog and journal storage."""

    @abstractmethod
    def load_catalog(self, name: str) -> Catalog:
        """Load a named catalog."""

    @abstractmethod
    def save_catalog(self, name: str, catalog: Catalog) -> None:
        """Persist a named catalog."""

    @abstractmethod
    def append_journal(self, entries: Iterable[str]) -> None:
        """Append resumable transfer journal records."""

