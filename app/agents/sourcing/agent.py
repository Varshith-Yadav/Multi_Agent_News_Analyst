from datetime import UTC, datetime

from app.graph.state import NewsState
from app.integration.news_api import fetch_news
from app.integration.rss import fetch_rss_news
from app.core.logging import audit_log
from app.services.article_service import get_articles_by_query
from app.services.ingestion_service import save_articles
from app.services.search_service import semantic_search
from app.utils.dedup import remove_duplicates


def _to_utc_iso(value: str | None) -> str:
    if not value:
        return datetime.now(UTC).isoformat()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    except Exception:
        return datetime.now(UTC).isoformat()


def sourcing_agent(state: NewsState):
    query = state["query"]
    report_region = state.get("region")
    report_industry = state.get("industry")
    time_window_hours = int(state.get("time_window_hours", 72))

    fresh_articles = []
    semantic_results = []
    db_results = []

    try:
        fresh_articles = fetch_news(query, region=report_region, industry=report_industry)
    except Exception:
        fresh_articles = []

    if not fresh_articles:
        try:
            fresh_articles = fetch_rss_news(
                query,
                region=report_region,
                industry=report_industry,
                limit=20,
            )
        except Exception:
            fresh_articles = []

    if fresh_articles:
        try:
            save_articles(fresh_articles)
        except Exception:
            pass

    try:
        semantic_results = semantic_search(query, k=12)
    except Exception:
        semantic_results = []

    try:
        db_results = get_articles_by_query(
            query,
            limit=25,
            region=report_region,
            industry=report_industry,
            time_window_hours=time_window_hours,
        )
    except Exception:
        db_results = []

    articles = remove_duplicates([*fresh_articles, *semantic_results, *db_results])
    normalized_articles = []
    for article in articles:
        normalized_articles.append(
            {
                "id": article.get("id"),
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "Unknown"),
                "url": article.get("url", ""),
                "published_at": _to_utc_iso(article.get("published_at")),
                "region": article.get("region") or report_region,
                "industry": article.get("industry") or report_industry,
            }
        )

    if not normalized_articles:
        normalized_articles.append(
            {
                "id": None,
                "title": f"Topic overview: {query}",
                "content": query,
                "source": "synthetic",
                "url": "",
                "published_at": _to_utc_iso(None),
                "region": report_region,
                "industry": report_industry,
            }
        )

    audit_log(
        "agent_sourcing",
        {
            "query": query,
            "report_region": report_region,
            "report_industry": report_industry,
            "time_window_hours": time_window_hours,
            "fresh_articles": len(fresh_articles),
            "retrieved_articles": len(normalized_articles),
        },
    )

    return {"articles": normalized_articles[:25]}
