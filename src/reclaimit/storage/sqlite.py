"""SQLite-backed catalog and journal storage scaffold."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from reclaimit.core.interfaces import CatalogStore
from reclaimit.core.models import Catalog


class SQLiteCatalogStore(CatalogStore):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def load_catalog(self, name: str) -> Catalog:
        # Catalog serialization lands with provider implementations.
        return Catalog()

    def save_catalog(self, name: str, catalog: Catalog) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "insert into catalogs(name, item_count) values(?, ?) "
                "on conflict(name) do update set item_count=excluded.item_count",
                (name, len(catalog.items)),
            )

    def append_journal(self, entries: Iterable[str]) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.executemany(
                "insert into journal(entry) values(?)",
                [(entry,) for entry in entries],
            )

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "create table if not exists catalogs("
                "name text primary key, item_count integer not null)"
            )
            connection.execute(
                "create table if not exists journal("
                "id integer primary key autoincrement, entry text not null, "
                "created_at text not null default current_timestamp)"
            )

