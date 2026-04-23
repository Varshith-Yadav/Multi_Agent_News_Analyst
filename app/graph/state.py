from typing import Any, TypedDict

from app.schemas.query import ReportFormat


class NewsState(TypedDict, total=False):
    query: str
    report_format: ReportFormat
    region: str | None
    industry: str | None
    time_window_hours: int
    articles: list[dict[str, Any]]
    summary: str
    sentiment: str
    sentiment_conf: float
    trends: list[str]
    trend_analysis: list[dict[str, Any]]
    credibility_scores: list[dict[str, Any]]
    credibility_score: float
    claims: list[dict[str, Any]]
    verification_results: list[dict[str, Any]]
    verified: list[dict[str, Any]]
    source_attribution: list[dict[str, Any]]
    confidence_score: float
    report: dict[str, Any]


def get_initial_state(
    query: str,
    report_format: ReportFormat = ReportFormat.brief_summary,
    region: str | None = None,
    industry: str | None = None,
    time_window_hours: int = 72,
) -> NewsState:
    return {
        "query": query,
        "report_format": report_format,
        "region": region,
        "industry": industry,
        "time_window_hours": time_window_hours,
        "articles": [],
        "summary": "",
        "sentiment": "",
        "sentiment_conf": 0.0,
        "trends": [],
        "trend_analysis": [],
        "credibility_scores": [],
        "credibility_score": 0.0,
        "claims": [],
        "verification_results": [],
        "verified": [],
        "source_attribution": [],
        "confidence_score": 0.0,
        "report": {},
    }
