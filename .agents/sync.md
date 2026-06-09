# Sync Agent Notes

- Planner output must be deterministic.
- Dry-run and execute modes must share the same plan-generation path.
- Conflict policies are `skip`, `overwrite_local`, `overwrite_device`, and `copy_as_new`.
- Represent deletes with tombstones in catalogs so known deletions differ from unseen files.
- Keep catalog, plan, plan entry, and media item structures as frozen Pydantic models.
- Journals must be append-only and resumable.

