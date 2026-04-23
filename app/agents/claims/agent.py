import re
from typing import Any

from app.core.llm import call_llm_json
from app.core.logging import audit_log
from app.graph.state import NewsState


def _fallback_claims(summary: str) -> list[dict[str, Any]]:
    sentences = re.split(r"(?<=[.!?])\s+", summary)
    claims = []
    for index, sentence in enumerate(sentences):
        text = sentence.strip()
        if len(text.split()) < 7:
            continue
        claim_type = "event"
        if re.search(r"\d", text):
            claim_type = "statistic"
        claims.append({"claim_id": f"c{index+1}", "claim": text, "type": claim_type})
        if len(claims) >= 6:
            break
    return claims


def claims_agent(state: NewsState):
    summary = state.get("summary", "")
    if not summary:
        return {"claims": []}

    prompt = f"""
Extract factual claims from this summary and return JSON only.

JSON schema:
{{
  "claims": [
    {{
      "claim_id": "c1",
      "claim": "factual statement",
      "type": "fact|statistic|event"
    }}
  ]
}}

Summary:
{summary}
"""

    try:
        data = call_llm_json(prompt)
        raw_claims = data.get("claims", []) if isinstance(data, dict) else []
        claims: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_claims):
            claim_text = str(item.get("claim", "")).strip()
            if not claim_text:
                continue
            claims.append(
                {
                    "claim_id": item.get("claim_id") or f"c{idx+1}",
                    "claim": claim_text,
                    "type": str(item.get("type", "fact")).lower(),
                }
            )
        if not claims:
            claims = _fallback_claims(summary)
    except Exception:
        claims = _fallback_claims(summary)

    audit_log("agent_claims", {"claims_extracted": len(claims)})
    return {"claims": claims}
