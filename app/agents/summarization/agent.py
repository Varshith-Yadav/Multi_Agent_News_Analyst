from app.core.llm import call_llm, call_llm_json
from app.core.logging import audit_log
from app.schemas.agent_outputs import SummaryOutput
from app.services.compliance_service import copyright_safe_text


def _build_prompt(content: str, report_format: str) -> str:
    return f"""
You are generating a news intelligence summary.
Report format: {report_format}

Constraints:
- Paraphrase source material. Do not copy long passages.
- Keep it factual and attributed where possible.
- Return JSON only.

JSON schema:
{{
  "summary": "A concise synthesis tailored to the report format."
}}

Content:
{content}
"""


def summarize_agent(state):
    articles = state.get("articles", [])
    content = " ".join([article.get("content", "") for article in articles]) or state["query"]
    report_format = str(state.get("report_format", "brief_summary"))

    try:
        data = call_llm_json(_build_prompt(content, report_format))
        if isinstance(data, dict) and data.get("summary"):
            validated = SummaryOutput(**data)
        else:
            raise ValueError("Missing summary field in LLM JSON response")
    except Exception:
        fallback_summary = ""
        try:
            # Try a raw non-JSON LLM call if JSON schema failed
            fallback_summary = call_llm(
                "Summarize this news topic in 3 concise factual sentences:\n\n"
                f"{content}"
            ).strip()
            # If the fallback returned the prompt itself (due to stub fallback), clear it
            if fallback_summary.startswith("Summarize this news topic"):
                fallback_summary = ""
        except Exception:
            pass

        if not fallback_summary:
            sentences = [segment.strip() for segment in content.replace('\n', '. ').split(".") if segment.strip()]
            fallback_summary = ". ".join(sentences[:3]).strip()
            if fallback_summary and not fallback_summary.endswith("."):
                fallback_summary += "."

        validated = SummaryOutput(summary=fallback_summary or content[:500])

    safe_summary = copyright_safe_text(validated.summary)
    audit_log(
        "agent_summarization",
        {
            "report_format": report_format,
            "article_count": len(articles),
            "summary_words": len(safe_summary.split()),
        },
    )
    return {"summary": safe_summary}
