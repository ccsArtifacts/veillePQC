from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed

from veille_pqc.models import Item, SourceConfig


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def _download(url: str) -> str:
    headers = {
        "User-Agent": "veille-pqc/0.1 (+https://local.tooling)",
    }
    with httpx.Client(timeout=20, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _same_domain(base_url: str, candidate_url: str) -> bool:
    return urlparse(base_url).netloc == urlparse(candidate_url).netloc


def collect(source: SourceConfig) -> list[Item]:
    html = _download(str(source.url))
    soup = BeautifulSoup(html, "html.parser")

    include_patterns = [p.lower() for p in source.include_patterns]
    results: list[Item] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = urljoin(str(source.url), a["href"])
        title = _normalize_spaces(a.get_text(" "))
        haystack = f"{title} {href}".lower()

        if not title or len(title) < 8:
            continue
        if href in seen:
            continue
        if not _same_domain(str(source.url), href):
            continue
        if include_patterns and not any(pattern in haystack for pattern in include_patterns):
            continue

        seen.add(href)
        results.append(
            Item(
                source_name=source.name,
                title=title,
                url=href,
                summary="",
                tags=source.tags.copy(),
            )
        )
        if len(results) >= source.max_items:
            break

    return results
