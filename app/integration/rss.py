from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

import feedparser


def _to_iso(value: Any) -> str:
    if value is None:
        return datetime.now(UTC).isoformat()
    try:
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime(*value[:6], tzinfo=UTC)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    except Exception:
        return datetime.now(UTC).isoformat()


def _entry_to_article(entry: Any, region: str | None, industry: str | None) -> dict[str, Any]:
    summary = (getattr(entry, "summary", "") or "").strip()
    title = (getattr(entry, "title", "") or "").strip()
    content = summary if summary else title

    return {
        "title": title,
        "content": content,
        "source": "Google News RSS",
        "url": (getattr(entry, "link", "") or "").strip(),
        "published_at": _to_iso(getattr(entry, "published_parsed", None)),
        "region": region,
        "industry": industry,
    }


def fetch_rss_news(
    query: str,
    *,
    limit: int = 20,
    region: str | None = None,
    industry: str | None = None,
) -> list[dict[str, Any]]:
    q = " ".join(part for part in [query, region, industry] if part).strip() or query
    url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)
    if getattr(feed, "bozo", False):
        return []

    articles: list[dict[str, Any]] = []
    for entry in getattr(feed, "entries", [])[:limit]:
        article = _entry_to_article(entry, region, industry)
        if article["url"] and article["title"]:
            articles.append(article)

    return articles
