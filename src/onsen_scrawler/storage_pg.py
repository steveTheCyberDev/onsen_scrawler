"""Postgres writer for OnsenSpring records using psycopg v3."""
from __future__ import annotations

import re
from datetime import datetime, timezone

import psycopg
from psycopg import Connection

from .models import OnsenSpring

_QUALITY_SPLIT_RE = re.compile(r"[、,，]")


class PostgresStorage:
    """
    Write OnsenSpring records into the three-table Postgres schema.

    The caller owns the connection lifecycle (open / close / commit /
    rollback). Call flush() or close() before the final conn.commit().
    """

    def __init__(self, conn: Connection, *, batch_size: int = 100) -> None:
        self._conn = conn
        self._batch_size = batch_size
        self._pending: list[tuple[OnsenSpring, str]] = []

    def write(self, spring: OnsenSpring, region_slug: str) -> None:
        """Queue one record. Flushes automatically when batch is full."""
        self._pending.append((spring, region_slug))
        if len(self._pending) >= self._batch_size:
            self.flush()

    def flush(self) -> int:
        """Flush pending records. Returns the number of records processed."""
        if not self._pending:
            return 0
        batch = self._pending[:]
        self._pending.clear()
        with self._conn.transaction():
            for spring, region_slug in batch:
                self._upsert_one(spring, region_slug)
        return len(batch)

    def close(self) -> None:
        """Flush remaining records. Caller still owns the connection."""
        self.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _upsert_one(self, spring: OnsenSpring, region_slug: str) -> None:
        spring_id = self._upsert_spring(spring, region_slug)
        if spring.spa_quality:
            for token in self._split_quality(spring.spa_quality):
                type_id = self._get_or_create_quality_type(token)
                self._link_quality(spring_id, type_id)

    def _upsert_spring(self, spring: OnsenSpring, region_slug: str) -> int:
        prefecture, city = self._split_location(spring.location or "")
        row = self._conn.execute(
            """
            INSERT INTO onsen_springs
                (detail_url, name, prefecture, city, sales_point,
                 region_slug, source_url, fetched_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (detail_url) DO UPDATE SET
                name        = EXCLUDED.name,
                prefecture  = EXCLUDED.prefecture,
                city        = EXCLUDED.city,
                sales_point = EXCLUDED.sales_point,
                region_slug = EXCLUDED.region_slug,
                source_url  = EXCLUDED.source_url,
                fetched_at  = EXCLUDED.fetched_at
            RETURNING id
            """,
            (
                spring.detail_url,
                spring.name,
                prefecture,
                city,
                spring.sales_point,
                region_slug,
                spring.source_url,
                datetime.now(timezone.utc),
            ),
        ).fetchone()
        return row[0]  # type: ignore[index]

    def _get_or_create_quality_type(self, name: str) -> int:
        row = self._conn.execute(
            """
            INSERT INTO spa_quality_types (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (name,),
        ).fetchone()
        return row[0]  # type: ignore[index]

    def _link_quality(self, spring_id: int, type_id: int) -> None:
        self._conn.execute(
            """
            INSERT INTO onsen_spring_qualities (spring_id, spa_quality_type_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (spring_id, type_id),
        )

    @staticmethod
    def _split_location(location: str) -> tuple[str, str]:
        parts = location.split(" ", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else (location, "")

    @staticmethod
    def _split_quality(spa_quality: str) -> list[str]:
        return [t.strip() for t in _QUALITY_SPLIT_RE.split(spa_quality) if t.strip()]
