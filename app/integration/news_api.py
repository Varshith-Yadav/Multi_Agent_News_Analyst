from datetime import UTC, datetime
import os
from typing import Any

import requests
from dateutil import parser as date_parser


API_KEY = os.getenv("NEWS_API_KEY")


def _parse_datetime(value: str | None) -> str:
    if not value:
        return datetime.now(UTC).isoformat()
    try:
        parsed = date_parser.parse(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    except Exception:
        return datetime.now(UTC).isoformat()


def fetch_news(
    query: str,
    *,
    page_size: int = 10,
    region: str | None = None,
    industry: str | None = None,
) -> list[dict[str, Any]]:
    if not API_KEY:
        return []

    url = "https://newsapi.org/v2/everything"
    composed_query = " ".join(part for part in [query, region, industry] if part).strip()

    params = {
        "q": composed_query or query,
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": page_size,
        "sortBy": "publishedAt",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    articles = []
    for item in data.get("articles", []):
        articles.append(
            {
                "title": (item.get("title") or "").strip(),
                "content": (item.get("content") or item.get("description") or "").strip(),
                "source": (item.get("source") or {}).get("name", "Unknown"),
                "url": item.get("url") or "",
                "published_at": _parse_datetime(item.get("publishedAt")),
                "region": region,
                "industry": industry,
            }
        )

    return [article for article in articles if article["url"] and article["title"]]
