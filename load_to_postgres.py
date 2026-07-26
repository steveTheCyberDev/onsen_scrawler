"""
Load all data/*_springs.jsonl files into Postgres.

Usage:
    python3 load_to_postgres.py
    DATABASE_URL=postgresql://user:pass@host/db python3 load_to_postgres.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).parent / "src"))

from onsen_scrawler.config import SETTINGS
from onsen_scrawler.models import OnsenSpring
from onsen_scrawler.storage_pg import PostgresStorage

DATA_DIR = Path(__file__).parent / "data"
SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def derive_slug(path: Path) -> str:
    return path.stem.replace("_springs", "")


def apply_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.commit()
    print("Schema applied.")


def load_file(storage: PostgresStorage, path: Path) -> tuple[int, int]:
    slug = derive_slug(path)
    loaded = skipped = 0
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"  [warn] {path.name}:{lineno}: {exc}", file=sys.stderr)
                skipped += 1
                continue
            if not obj.get("detail_url"):
                print(f"  [warn] {path.name}:{lineno}: missing detail_url, skipping", file=sys.stderr)
                skipped += 1
                continue
            spring = OnsenSpring(
                source_url=obj["source_url"],
                name=obj.get("name"),
                location=obj.get("location"),
                spa_quality=obj.get("spa_quality"),
                sales_point=obj.get("sales_point"),
                detail_url=obj["detail_url"],
            )
            storage.write(spring, slug)
            loaded += 1
    storage.flush()
    return loaded, skipped


def main() -> None:
    spring_files = sorted(DATA_DIR.glob("*_springs.jsonl"))
    if not spring_files:
        print("No *_springs.jsonl files found in data/.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to: {SETTINGS.db_url}")
    with psycopg.connect(SETTINGS.db_url) as conn:
        apply_schema(conn)
        storage = PostgresStorage(conn, batch_size=100)
        total_loaded = total_skipped = 0

        for path in spring_files:
            print(f"Loading {path.name} ...", end="  ", flush=True)
            loaded, skipped = load_file(storage, path)
            total_loaded += loaded
            total_skipped += skipped
            print(f"{loaded} loaded, {skipped} skipped")

        conn.commit()

    print(f"\nDone. Total: {total_loaded} loaded, {total_skipped} skipped.")


if __name__ == "__main__":
    main()
