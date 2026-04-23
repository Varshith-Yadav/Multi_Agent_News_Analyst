from statistics import mean
from typing import Any

from app.schemas.query import ReportFormat
from app.services.compliance_service import copyright_safe_text


def _as_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value * 100)}%"


def _top_sources(source_attribution: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    sorted_sources = sorted(
        source_attribution,
        key=lambda item: (
            item.get("verification_status") == "supported",
            item.get("credibility_score", 0),
        ),
        reverse=True,
    )
    return sorted_sources[:limit]


def _build_quick_brief(state: dict[str, Any]) -> list[str]:
    verification_results = state.get("verification_results", [])
    verified_count = len([item for item in verification_results if item.get("verification_status") == "verified"])
    partial_count = len(
        [item for item in verification_results if item.get("verification_status") == "partially_verified"]
    )

    trend_analysis = state.get("trend_analysis", [])
    top_trend = trend_analysis[0]["keyword"] if trend_analysis else "no dominant spike"
    top_trend_spike = trend_analysis[0]["spike_score"] if trend_analysis else "n/a"

    return [
        f"Overall sentiment is {state.get('sentiment', 'neutral')} with {_as_percent(state.get('sentiment_conf'))} classifier confidence.",
        f"Cross-verification found {verified_count} fully verified and {partial_count} partially verified claims.",
        f"Highest narrative spike: {top_trend} (spike score {top_trend_spike}).",
        f"Source credibility aggregate score: {_as_percent(state.get('credibility_score'))}.",
        f"Final confidence score for this report: {_as_percent(state.get('confidence_score'))}.",
    ]


def _source_summary(source_attribution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in source_attribution:
        grouped.setdefault(item.get("source", "unknown"), []).append(item)

    summary = []
    for source, records in grouped.items():
        scores = [record.get("credibility_score", 0) for record in records]
        statuses = [record.get("verification_status") for record in records]
        summary.append(
            {
                "source": source,
                "article_count": len(records),
                "avg_credibility": round(mean(scores), 2) if scores else 0.0,
                "verification_status": "supported" if "supported" in statuses else "pending",
                "latest_publication": max(
                    (record.get("published_at") for record in records if record.get("published_at")),
                    default=None,
                ),
                "sample_urls": [record.get("url") for record in records if record.get("url")][:2],
            }
        )
    return sorted(summary, key=lambda item: item["avg_credibility"], reverse=True)


def build_report(state: dict[str, Any]) -> dict[str, Any]:
    report_format = ReportFormat(state.get("report_format", ReportFormat.brief_summary))
    summary = copyright_safe_text(state.get("summary", ""))
    quick_brief = _build_quick_brief(state)
    source_attribution = state.get("source_attribution", [])
    top_sources = _top_sources(source_attribution)
    source_summary = _source_summary(source_attribution)
    verification_results = state.get("verification_results", [])
    trends = state.get("trends", [])
    trend_analysis = state.get("trend_analysis", [])

    report: dict[str, Any] = {
        "report_format": report_format.value,
        "summary": summary,
        "quick_brief": quick_brief,
        "sentiment": state.get("sentiment"),
        "sentiment_confidence": state.get("sentiment_conf"),
        "trends": trends,
        "trend_analysis": trend_analysis,
        "credibility": state.get("credibility_score"),
        "confidence": state.get("confidence_score"),
        "verified_claims": verification_results,
        "verification_status": {
            "required_sources_per_claim": 3,
            "verified_claim_count": len(
                [item for item in verification_results if item.get("verification_status") == "verified"]
            ),
            "total_claim_count": len(verification_results),
        },
        "source_attribution": top_sources,
        "source_summary": source_summary,
    }

    if report_format == ReportFormat.brief_summary:
        report["summary"] = " ".join(quick_brief[:3])
    elif report_format == ReportFormat.executive_summary:
        report["executive_summary"] = summary
        report["summary"] = " ".join(quick_brief[:4])
    elif report_format == ReportFormat.deep_analytical_report:
        report["deep_dive"] = {
            "context": summary,
            "trend_evolution": trend_analysis,
            "verification_matrix": verification_results,
            "source_credibility_breakdown": source_summary,
        }
    elif report_format == ReportFormat.daily_digest:
        report["daily_digest"] = quick_brief
        report["summary"] = " ".join(quick_brief)
    elif report_format == ReportFormat.weekly_trend_report:
        report["weekly_trend_report"] = {
            "top_spikes": trend_analysis[:5],
            "narrative_evolution": [
                {"keyword": item.get("keyword"), "evolution": item.get("evolution")}
                for item in trend_analysis[:5]
            ],
            "source_mix": source_summary[:5],
        }
    elif report_format == ReportFormat.real_time_alert:
        critical_claims = [
            item
            for item in verification_results
            if item.get("verification_status") in {"unverified", "weakly_supported"}
        ]
        report["alerts"] = [
            {
                "type": "verification_risk",
                "message": f"Claim '{item.get('claim')}' has status {item.get('verification_status')}.",
                "confidence": item.get("confidence"),
            }
            for item in critical_claims[:5]
        ]
        report["summary"] = " ".join(quick_brief[:2])
    elif report_format == ReportFormat.industry_snapshot:
        report["industry_snapshot"] = {
            "industry": state.get("industry"),
            "summary": summary,
            "top_trends": trend_analysis[:5],
            "key_sources": source_summary[:5],
        }

    return report
