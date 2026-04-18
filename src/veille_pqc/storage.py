from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from veille_pqc.models import Item


SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    url TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    published TEXT,
    tags_json TEXT,
    score INTEGER,
    matched_keywords_json TEXT,
    category TEXT,
    sector_tags_json TEXT,
    raw_json TEXT
);
"""


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(items)")}
    if "category" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN category TEXT DEFAULT 'other'")
    if "sector_tags_json" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN sector_tags_json TEXT DEFAULT '[]'")
    conn.commit()


def open_db(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    _ensure_schema(conn)
    return conn


def upsert_items(conn: sqlite3.Connection, items: list[Item]) -> int:
    inserted = 0
    for item in items:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO items (
                url, source_name, title, summary, published,
                tags_json, score, matched_keywords_json, category, sector_tags_json, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.url,
                item.source_name,
                item.title,
                item.summary,
                item.published.isoformat() if item.published else None,
                json.dumps(item.tags, ensure_ascii=False),
                item.score,
                json.dumps(item.matched_keywords, ensure_ascii=False),
                item.category,
                json.dumps(item.sector_tags, ensure_ascii=False),
                json.dumps(item.raw, ensure_ascii=False),
            ),
        )
        if cursor.rowcount:
            inserted += 1
    conn.commit()
    return inserted
