from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class SourceConfig(BaseModel):
    name: str
    type: Literal["rss", "webpage"]
    url: HttpUrl
    include_patterns: list[str] = Field(default_factory=list)
    max_items: int = 15
    tags: list[str] = Field(default_factory=list)


class KeywordsConfig(BaseModel):
    high_priority: list[str] = Field(default_factory=list)
    medium_priority: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    keywords: KeywordsConfig
    categories: dict[str, list[str]] = Field(default_factory=dict)
    sectors: dict[str, list[str]] = Field(default_factory=dict)
    sources: list[SourceConfig]


class Item(BaseModel):
    source_name: str
    title: str
    url: str
    summary: str = ""
    published: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    score: int = 0
    matched_keywords: list[str] = Field(default_factory=list)
    category: str = "other"
    sector_tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
