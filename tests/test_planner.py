from datetime import UTC, datetime
from pathlib import PurePosixPath

from reclaimit.core import (
    Catalog,
    ConflictPolicy,
    MediaItem,
    SyncAction,
    SyncDirection,
    SyncPlanner,
)


def item(path: str, size: int, checksum: str | None = None, deleted: bool = False) -> MediaItem:
    return MediaItem(
        path=PurePosixPath(path),
        size=size,
        checksum=checksum,
        modified_at=datetime(2026, 1, 1, tzinfo=UTC),
        deleted=deleted,
    )


def test_new_source_file_copies_to_target_in_bidirectional_plan():
    plan = SyncPlanner().plan(
        Catalog.from_items([item("/a.jpg", 10)]),
        Catalog(),
        direction=SyncDirection.BIDIRECTIONAL,
    )

    assert [entry.action for entry in plan.entries] == [SyncAction.COPY_TO_TARGET]


def test_same_file_is_skipped():
    source = Catalog.from_items([item("/a.jpg", 10, "abc")])
    target = Catalog.from_items([item("/a.jpg", 999, "abc")])

    plan = SyncPlanner().plan(source, target)

    assert [entry.action for entry in plan.entries] == [SyncAction.SKIP]


def test_changed_file_conflicts_by_default():
    source = Catalog.from_items([item("/a.jpg", 10, "abc")])
    target = Catalog.from_items([item("/a.jpg", 10, "def")])

    plan = SyncPlanner().plan(source, target)

    assert plan.has_conflicts
    assert plan.entries[0].action == SyncAction.CONFLICT


def test_conflict_policy_copy_as_new_sets_destination_path():
    source = Catalog.from_items([item("/a.jpg", 10, "abc")])
    target = Catalog.from_items([item("/a.jpg", 10, "def")])

    plan = SyncPlanner().plan(source, target, conflict_policy=ConflictPolicy.COPY_AS_NEW)

    assert plan.entries[0].action == SyncAction.COPY_TO_TARGET
    assert plan.entries[0].destination_path == PurePosixPath("/a.conflict-copy.jpg")


def test_deleted_source_propagates_in_local_to_device_direction():
    source = Catalog.from_items([item("/a.jpg", 10, deleted=True)])
    target = Catalog.from_items([item("/a.jpg", 10)])

    plan = SyncPlanner().plan(source, target, direction=SyncDirection.LOCAL_TO_DEVICE)

    assert plan.entries[0].action == SyncAction.DELETE_FROM_TARGET

