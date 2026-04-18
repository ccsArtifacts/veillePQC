from __future__ import annotations

from veille_pqc.models import Item


def _text(item: Item) -> str:
    return f"{item.title} {item.summary} {' '.join(item.tags)} {item.url}".lower()


def classify_category(item: Item, category_keywords: dict[str, list[str]]) -> Item:
    text = _text(item)
    best_category = "other"
    best_score = 0
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword.lower() in text)
        if score > best_score:
            best_category = category
            best_score = score
    item.category = best_category
    return item


def classify_sectors(item: Item, sector_keywords: dict[str, list[str]]) -> Item:
    text = _text(item)
    sectors: list[str] = []
    for sector, keywords in sector_keywords.items():
        if any(keyword.lower() in text for keyword in keywords):
            sectors.append(sector)
    item.sector_tags = sectors
    return item
