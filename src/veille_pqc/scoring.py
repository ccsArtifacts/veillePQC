from __future__ import annotations

import re
from datetime import datetime, timezone

from veille_pqc.models import Item, KeywordsConfig


def _text(item: Item) -> str:
    return f"{item.title} {item.summary} {' '.join(item.tags)} {item.url}".lower()


def score_item(item: Item, keywords: KeywordsConfig) -> Item:
    text = _text(item)
    matched: list[str] = []
    score = 0

    for keyword in keywords.high_priority:
        if keyword.lower() in text:
            score += 15
            matched.append(keyword)

    for keyword in keywords.medium_priority:
        if keyword.lower() in text:
            score += 7
            matched.append(keyword)

    if item.published:
        now = datetime.now(timezone.utc)
        delta_days = (now - item.published).days
        if delta_days <= 7:
            score += 10
        elif delta_days <= 30:
            score += 6
        elif delta_days <= 90:
            score += 3

    domain_boosts = {
        "nist.gov": 10,
        "cisa.gov": 9,
        "nsa.gov": 9,
        "enisa.europa.eu": 8,
        "etsi.org": 8,
        "ietf.org": 8,
        "datatracker.ietf.org": 8,
        "pqca.org": 5,
        "openquantumsafe.org": 5,
        "arxiv.org": 4,
    }

    for domain, domain_score in domain_boosts.items():
        if domain in item.url:
            score += domain_score
            break

    item.score = score
    item.matched_keywords = sorted(set(matched), key=str.lower)
    return item


def classify_priority(item: Item) -> str:
    if item.score >= 35:
        return "critical"
    if item.score >= 22:
        return "high"
    if item.score >= 12:
        return "medium"
    return "low"
