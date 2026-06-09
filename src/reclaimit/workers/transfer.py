"""Plan execution scaffolding with resumable journal events."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from pydantic import BaseModel, ConfigDict

from reclaimit.core.models import SyncAction, SyncPlan, SyncPlanEntry
from reclaimit.workers.events import EventKind, WorkerEvent


class JournalEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: SyncAction
    path: str
    completed: bool


class PlanTransferExecutor:
    """Execute plan entries through injectable operation callbacks."""

    def __init__(
        self,
        *,
        perform: Callable[[SyncPlanEntry], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> None:
        self._perform = perform or (lambda entry: None)
        self._should_cancel = should_cancel or (lambda: False)
        self.journal: list[JournalEntry] = []

    def execute(self, plan: SyncPlan) -> Iterator[WorkerEvent]:
        entries = plan.actionable_entries
        total = len(entries)
        yield WorkerEvent(kind=EventKind.STATUS, message="starting transfer", total=total)

        for index, entry in enumerate(entries, start=1):
            if self._should_cancel():
                yield WorkerEvent(
                    kind=EventKind.CANCELLED,
                    message="transfer cancelled",
                    current=index - 1,
                    total=total,
                )
                return

            if entry.action in {SyncAction.CONFLICT, SyncAction.SKIP}:
                yield WorkerEvent(
                    kind=EventKind.WARNING,
                    message=f"unhandled entry: {entry.reason}",
                    current=index,
                    total=total,
                )
                continue

            if plan.dry_run:
                self._record(entry, completed=False)
                yield WorkerEvent(
                    kind=EventKind.PROGRESS,
                    message="planned",
                    current=index,
                    total=total,
                )
                continue

            try:
                self._perform(entry)
            except Exception as exc:  # noqa: BLE001 - normalize into event stream here.
                yield WorkerEvent(
                    kind=EventKind.ERROR,
                    message="transfer failed",
                    current=index,
                    total=total,
                    detail=str(exc),
                )
                return

            self._record(entry, completed=True)
            yield WorkerEvent(
                kind=EventKind.PROGRESS,
                message="transferred",
                current=index,
                total=total,
            )

        yield WorkerEvent(
            kind=EventKind.COMPLETE,
            message="transfer complete",
            current=total,
            total=total,
        )

    def _record(self, entry: SyncPlanEntry, *, completed: bool) -> None:
        item = entry.source or entry.target
        self.journal.append(
            JournalEntry(
                action=entry.action,
                path=item.identity if item else "",
                completed=completed,
            )
        )
