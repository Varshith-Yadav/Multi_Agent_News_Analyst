from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

from app.core.logging import audit_log
from app.graph.state import NewsState

SOURCE_BASELINES = {
    "reuters": 0.93,
    "associated press": 0.92,
    "ap news": 0.92,
    "bbc": 0.89,
    "financial times": 0.9,
    "wall street journal": 0.88,
    "new york times": 0.86,
    "bloomberg": 0.9,
}


def _source_key(article: dict[str, Any]) -> str:
    source = (article.get("source") or "").strip().lower()
    if source:
        return source
    domain = urlparse(article.get("url", "")).netloc.lower()
    return domain or "unknown"


def _article_quality(article: dict[str, Any]) -> float:
    title_length = len((article.get("title") or "").split())
    content_length = len((article.get("content") or "").split())
    has_url = bool(article.get("url"))
    has_date = bool(article.get("published_at"))

    score = 0.45
    if title_length >= 6:
        score += 0.1
    if content_length >= 80:
        score += 0.15
    if has_url:
        score += 0.05
    if has_date:
        score += 0.05
    return min(0.95, round(score, 2))


def credibility_agent(state: NewsState):
    articles = state.get("articles", [])
    if not articles:
        return {"credibility_scores": [], "credibility_score": 0.0, "source_attribution": []}

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for article in articles:
        grouped[_source_key(article)].append(article)

    source_results = []
    attribution = []

    for source_name, source_articles in grouped.items():
        baseline = SOURCE_BASELINES.get(source_name, 0.62)
        quality_scores = [_article_quality(item) for item in source_articles]
        avg_quality = sum(quality_scores) / max(1, len(quality_scores))
        source_score = round(min(0.97, (0.7 * baseline) + (0.3 * avg_quality)), 2)

        source_results.append(
            {
                "source": source_name,
                "article_count": len(source_articles),
                "baseline_score": round(baseline, 2),
                "quality_score": round(avg_quality, 2),
                "credibility_score": source_score,
            }
        )

        for article in source_articles:
            attribution.append(
                {
                    "source": source_name,
                    "title": article.get("title"),
                    "url": article.get("url"),
                    "published_at": article.get("published_at"),
                    "credibility_score": source_score,
                    "verification_status": "pending",
                }
            )

    overall = round(
        sum(item["credibility_score"] * item["article_count"] for item in source_results)
        / max(1, sum(item["article_count"] for item in source_results)),
        2,
    )
    result = {
        "credibility_scores": source_results,
        "credibility_score": overall,
        "source_attribution": attribution,
    }
    audit_log(
        "agent_credibility",
        {
            "source_count": len(source_results),
            "overall_credibility": overall,
            "sources": [item["source"] for item in source_results],
        },
    )
    return result
