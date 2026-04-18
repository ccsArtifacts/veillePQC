from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from veille_pqc.models import Item, SourceConfig


def _parse_date(entry: dict) -> datetime | None:
    for field in ("published", "updated"):
        if value := entry.get(field):
            try:
                dt = parsedate_to_datetime(value)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def collect(source: SourceConfig) -> list[Item]:
    feed = feedparser.parse(str(source.url))
    items: list[Item] = []
    for entry in feed.entries[: source.max_items]:
        items.append(
            Item(
                source_name=source.name,
                title=entry.get("title", "(sans titre)"),
                url=entry.get("link", str(source.url)),
                summary=entry.get("summary", "") or entry.get("description", ""),
                published=_parse_date(entry),
                tags=source.tags.copy(),
                raw={"feed_source": feed.feed.get("title", "")},
            )
        )
    return items
