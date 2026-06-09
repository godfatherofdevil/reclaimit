"""Sync planning rules."""

from __future__ import annotations

from pathlib import PurePosixPath

from reclaimit.core.models import (
    Catalog,
    ConflictPolicy,
    SyncAction,
    SyncDirection,
    SyncPlan,
    SyncPlanEntry,
)


class SyncPlanner:
    """Compare source and target catalogs and produce a deterministic sync plan."""

    def plan(
        self,
        source: Catalog,
        target: Catalog,
        *,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        conflict_policy: ConflictPolicy = ConflictPolicy.SKIP,
        dry_run: bool = True,
    ) -> SyncPlan:
        source_items = source.by_identity()
        target_items = target.by_identity()
        entries: list[SyncPlanEntry] = []

        for identity in sorted(source_items.keys() | target_items.keys()):
            source_item = source_items.get(identity)
            target_item = target_items.get(identity)

            if source_item and source_item.deleted:
                entries.extend(self._deleted_source_entry(source_item, target_item, direction))
                continue

            if target_item and target_item.deleted:
                entries.extend(self._deleted_target_entry(source_item, target_item, direction))
                continue

            if source_item and not target_item:
                entries.append(
                    SyncPlanEntry(
                        action=self._copy_missing_from_source(direction),
                        source=source_item,
                        reason="missing on target",
                    )
                )
                continue

            if target_item and not source_item:
                entries.append(
                    SyncPlanEntry(
                        action=self._copy_missing_from_target(direction),
                        target=target_item,
                        reason="missing on source",
                    )
                )
                continue

            if source_item is None or target_item is None:
                continue

            if source_item.same_content_as(target_item):
                entries.append(
                    SyncPlanEntry(
                        action=SyncAction.SKIP,
                        source=source_item,
                        target=target_item,
                        reason="same content",
                    )
                )
                continue

            entries.append(
                self._changed_entry(source_item, target_item, direction, conflict_policy)
            )

        return SyncPlan(direction=direction, dry_run=dry_run, entries=tuple(entries))

    def _copy_missing_from_source(self, direction: SyncDirection) -> SyncAction:
        if direction == SyncDirection.DEVICE_TO_LOCAL:
            return SyncAction.COPY_TO_TARGET
        if direction == SyncDirection.LOCAL_TO_DEVICE:
            return SyncAction.SKIP
        return SyncAction.COPY_TO_TARGET

    def _copy_missing_from_target(self, direction: SyncDirection) -> SyncAction:
        if direction == SyncDirection.DEVICE_TO_LOCAL:
            return SyncAction.SKIP
        if direction == SyncDirection.LOCAL_TO_DEVICE:
            return SyncAction.COPY_TO_SOURCE
        return SyncAction.COPY_TO_SOURCE

    def _deleted_source_entry(self, source_item, target_item, direction: SyncDirection):
        if target_item is None:
            return [
                SyncPlanEntry(
                    action=SyncAction.SKIP,
                    source=source_item,
                    reason="deleted source has no target",
                )
            ]
        if direction == SyncDirection.LOCAL_TO_DEVICE:
            return [
                SyncPlanEntry(
                    action=SyncAction.DELETE_FROM_TARGET,
                    source=source_item,
                    target=target_item,
                    reason="source deletion propagates to target",
                )
            ]
        return [
            SyncPlanEntry(
                action=SyncAction.CONFLICT,
                source=source_item,
                target=target_item,
                reason="source deleted but target still exists",
            )
        ]

    def _deleted_target_entry(self, source_item, target_item, direction: SyncDirection):
        if source_item is None:
            return [
                SyncPlanEntry(
                    action=SyncAction.SKIP,
                    target=target_item,
                    reason="deleted target has no source",
                )
            ]
        if direction == SyncDirection.DEVICE_TO_LOCAL:
            return [
                SyncPlanEntry(
                    action=SyncAction.DELETE_FROM_SOURCE,
                    source=source_item,
                    target=target_item,
                    reason="target deletion propagates to source",
                )
            ]
        return [
            SyncPlanEntry(
                action=SyncAction.CONFLICT,
                source=source_item,
                target=target_item,
                reason="target deleted but source still exists",
            )
        ]

    def _changed_entry(self, source_item, target_item, direction, conflict_policy):
        if direction == SyncDirection.DEVICE_TO_LOCAL:
            return SyncPlanEntry(
                action=SyncAction.COPY_TO_TARGET,
                source=source_item,
                target=target_item,
                reason="changed on source",
            )
        if direction == SyncDirection.LOCAL_TO_DEVICE:
            return SyncPlanEntry(
                action=SyncAction.COPY_TO_SOURCE,
                source=source_item,
                target=target_item,
                reason="changed on target",
            )
        if conflict_policy == ConflictPolicy.OVERWRITE_LOCAL:
            return SyncPlanEntry(
                action=SyncAction.COPY_TO_TARGET,
                source=source_item,
                target=target_item,
                reason="conflict policy overwrites local",
            )
        if conflict_policy == ConflictPolicy.OVERWRITE_DEVICE:
            return SyncPlanEntry(
                action=SyncAction.COPY_TO_SOURCE,
                source=source_item,
                target=target_item,
                reason="conflict policy overwrites device",
            )
        if conflict_policy == ConflictPolicy.COPY_AS_NEW:
            return SyncPlanEntry(
                action=SyncAction.COPY_TO_TARGET,
                source=source_item,
                target=target_item,
                reason="conflict policy copies as new",
                destination_path=self._copy_as_new_path(source_item.path),
            )
        return SyncPlanEntry(
            action=SyncAction.CONFLICT,
            source=source_item,
            target=target_item,
            reason="changed on both sides",
        )

    def _copy_as_new_path(self, path: PurePosixPath) -> PurePosixPath:
        suffix = "".join(path.suffixes)
        stem = path.name[: -len(suffix)] if suffix else path.name
        return path.with_name(f"{stem}.conflict-copy{suffix}")

