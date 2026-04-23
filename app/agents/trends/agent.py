from collections import Counter
from datetime import datetime
import re
from typing import Any

from app.core.config import get_settings
from app.core.logging import audit_log
from app.graph.state import NewsState
from app.services.article_service import get_historical_articles

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "from",
    "by",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "this",
    "that",
    "it",
    "its",
    "their",
    "about",
    "after",
    "before",
    "into",
    "over",
    "under",
    "new",
    "news",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z]{3,}", (text or "").lower())
    return [token for token in tokens if token not in STOPWORDS]


def _freq_from_articles(articles: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for article in articles:
        text = f"{article.get('title', '')} {article.get('content', '')}"
        counter.update(_tokenize(text))
    return counter


def _evolution(articles: list[dict[str, Any]], keyword: str) -> str:
    if len(articles) < 4:
        return "stable"

    ordered = sorted(
        articles,
        key=lambda item: item.get("published_at", datetime.utcnow().isoformat()),
    )
    midpoint = len(ordered) // 2
    early = ordered[:midpoint]
    late = ordered[midpoint:]

    early_hits = sum(1 for item in early if keyword in _tokenize(f"{item.get('title')} {item.get('content')}"))
    late_hits = sum(1 for item in late if keyword in _tokenize(f"{item.get('title')} {item.get('content')}"))

    if late_hits >= early_hits + 2:
        return "accelerating"
    if early_hits >= late_hits + 2:
        return "cooling"
    return "stable"


def trends_agent(state: NewsState):
    articles = state.get("articles", [])
    if not articles:
        return {"trends": [], "trend_analysis": []}

    query = state.get("query", "")
    time_window_hours = int(state.get("time_window_hours", 72))
    settings = get_settings()

    historical = get_historical_articles(
        query=query,
        baseline_days=settings.trend_baseline_days,
        exclude_hours=time_window_hours,
    )

    current_freq = _freq_from_articles(articles)
    historical_freq = _freq_from_articles(historical)

    current_total = max(1, sum(current_freq.values()))
    historical_total = max(1, sum(historical_freq.values()))
    epsilon = 1e-6

    scored_keywords = []
    for keyword, count in current_freq.most_common(40):
        if count < 2:
            continue
        current_rate = count / current_total
        baseline_hits = historical_freq.get(keyword, 0)
        baseline_rate = baseline_hits / historical_total
        if baseline_hits == 0:
            spike_score = round(min(5.0, 1.0 + (count / 3)), 2)
        else:
            spike_score = round((current_rate + epsilon) / (baseline_rate + epsilon), 2)
        scored_keywords.append((keyword, spike_score, count))

    top_trends = sorted(scored_keywords, key=lambda item: (item[1], item[2]), reverse=True)[:8]
    trend_analysis = []
    for keyword, spike_score, mentions in top_trends:
        trend_analysis.append(
            {
                "keyword": keyword,
                "spike_score": spike_score,
                "mentions": mentions,
                "evolution": _evolution(articles, keyword),
            }
        )

    result = {
        "trends": [item["keyword"] for item in trend_analysis[:5]],
        "trend_analysis": trend_analysis,
    }
    audit_log(
        "agent_trends",
        {
            "query": query,
            "trend_count": len(result["trends"]),
            "top_trends": result["trends"],
        },
    )
    return result
