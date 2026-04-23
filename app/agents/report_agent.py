def report_agent(state):
    from app.core.logging import audit_log
    from app.services.report_service import build_report

    report = build_report(state)
    audit_log(
        "agent_report",
        {
            "report_format": report.get("report_format"),
            "confidence": report.get("confidence"),
            "source_count": len(report.get("source_attribution", [])),
        },
    )
    return {"report": report}
