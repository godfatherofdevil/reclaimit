from pathlib import PurePosixPath

from reclaimit.core import Catalog, MediaItem, SyncAction, SyncPlanner
from reclaimit.workers import EventKind, PlanTransferExecutor


def test_dry_run_emits_ordered_progress_and_complete_events():
    source = Catalog.from_items([MediaItem(path=PurePosixPath("/a.jpg"), size=1)])
    plan = SyncPlanner().plan(source, Catalog(), dry_run=True)

    events = list(PlanTransferExecutor().execute(plan))

    assert [event.kind for event in events] == [
        EventKind.STATUS,
        EventKind.PROGRESS,
        EventKind.COMPLETE,
    ]
    assert events[-1].current == 1


def test_cancellation_stops_before_transfer():
    source = Catalog.from_items([MediaItem(path=PurePosixPath("/a.jpg"), size=1)])
    plan = SyncPlanner().plan(source, Catalog(), dry_run=False)

    events = list(PlanTransferExecutor(should_cancel=lambda: True).execute(plan))

    assert events[-1].kind == EventKind.CANCELLED


def test_execute_records_completed_journal_entry():
    source = Catalog.from_items([MediaItem(path=PurePosixPath("/a.jpg"), size=1)])
    plan = SyncPlanner().plan(source, Catalog(), dry_run=False)
    executor = PlanTransferExecutor()

    list(executor.execute(plan))

    assert executor.journal[0].action == SyncAction.COPY_TO_TARGET
    assert executor.journal[0].completed is True

