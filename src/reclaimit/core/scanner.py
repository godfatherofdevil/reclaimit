"""Local filesystem media scanner."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from reclaimit.core.models import Catalog, MediaItem, MediaKind

PHOTO_EXTENSIONS = frozenset({".jpg", ".jpeg", ".heic", ".png"})
VIDEO_EXTENSIONS = frozenset({".mov", ".mp4", ".m4v"})


def scan_local_media(root: str | Path) -> Catalog:
    """Scan regular, non-hidden files below root into a media catalog."""
    root_path = Path(root).expanduser()
    items: list[MediaItem] = []

    for path in _iter_visible_files(root_path):
        stat = path.stat()
        relative_path = "/" + path.relative_to(root_path).as_posix()
        items.append(
            MediaItem(
                path=relative_path,
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                kind=_kind_for_path(path),
            )
        )

    return Catalog.from_items(items)


def _iter_visible_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            files.extend(_iter_visible_files(child))
        elif child.is_file():
            files.append(child)
    return files


def _kind_for_path(path: Path) -> MediaKind:
    suffix = path.suffix.lower()
    if suffix in PHOTO_EXTENSIONS:
        return MediaKind.PHOTO
    if suffix in VIDEO_EXTENSIONS:
        return MediaKind.VIDEO
    return MediaKind.OTHER
