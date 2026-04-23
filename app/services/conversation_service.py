from typing import Any

from app.core.llm import call_llm_json
from app.schemas.query import FollowupMode


def _source_lines(report: dict[str, Any]) -> str:
    lines = []
    for source in report.get("source_attribution", [])[:8]:
        lines.append(
            f"- {source.get('source')} | credibility={source.get('credibility_score')} | "
            f"verification={source.get('verification_status')} | url={source.get('url')}"
        )
    return "\n".join(lines) or "- No source attribution available."


def generate_followup_response(
    *,
    mode: FollowupMode,
    question: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    system_instructions = {
        FollowupMode.follow_up: (
            "Answer the follow-up question only from report evidence and source attribution. "
            "If evidence is missing, clearly say so."
        ),
        FollowupMode.refine_topic: (
            "Refine the user's topic into a sharper intelligence query and explain why it improves analysis."
        ),
        FollowupMode.opposing_viewpoints: (
            "Provide opposing viewpoints and narrative counter-arguments based on available sources."
        ),
    }

    prompt = f"""
You are a conversational news analyst assistant.
Mode: {mode.value}
Instruction: {system_instructions[mode]}

Current report format: {report.get("report_format")}
Summary: {report.get("summary")}
Quick brief: {report.get("quick_brief")}
Trends: {report.get("trends")}
Verification: {report.get("verification_status")}
Sources:
{_source_lines(report)}

User question:
{question}

Return JSON only:
{{
  "answer": "direct answer",
  "refined_query": "optional refined query string or null",
  "suggested_next_questions": ["question 1", "question 2", "question 3"]
}}
"""

    try:
        data = call_llm_json(prompt)
        answer = str(data.get("answer", "")).strip()
        refined_query = data.get("refined_query")
        next_questions = data.get("suggested_next_questions", [])
        if not answer:
            raise ValueError("Empty answer")
        return {
            "answer": answer,
            "refined_query": refined_query if isinstance(refined_query, str) else None,
            "suggested_next_questions": [str(item) for item in next_questions][:3],
        }
    except Exception:
        fallback_answer = (
            "The current report does not contain enough structured evidence to answer this with high confidence."
        )
        if mode == FollowupMode.refine_topic:
            fallback_answer = (
                "Use a narrower topic with entity + geography + timeframe for higher signal quality."
            )
        if mode == FollowupMode.opposing_viewpoints:
            fallback_answer = (
                "Opposing viewpoints cannot be reliably derived from this report alone; broaden sources before concluding."
            )
        return {
            "answer": fallback_answer,
            "refined_query": question if mode == FollowupMode.refine_topic else None,
            "suggested_next_questions": [
                "Which claims are weakly supported?",
                "Show source credibility breakdown.",
                "What trends are accelerating this week?",
            ],
        }
