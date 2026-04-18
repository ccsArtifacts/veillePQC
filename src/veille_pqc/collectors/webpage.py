from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from veille_pqc.models import Item, SourceConfig

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Retry uniquement sur les erreurs réseau, pas sur les 4xx."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, (httpx.TransportError, httpx.TimeoutException))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
)
def _download(url: str) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; veille-pqc/0.3; +https://github.com/ccsArtifacts/veillePQC)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        with httpx.Client(timeout=20, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            if response.status_code in (403, 401, 429):
                logger.warning("Source ignorée (%s) : HTTP %s pour %s", response.status_code, response.status_code, url)
                return None
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        logger.warning("Erreur HTTP %s pour %s — source ignorée.", e.response.status_code, url)
        return None


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _same_domain(base_url: str, candidate_url: str) -> bool:
    return urlparse(base_url).netloc == urlparse(candidate_url).netloc


def collect(source: SourceConfig) -> list[Item]:
    html = _download(str(source.url))
    if html is None:
        logger.warning("Source '%s' ignorée (accès refusé ou erreur réseau).", source.name)
        return []

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
