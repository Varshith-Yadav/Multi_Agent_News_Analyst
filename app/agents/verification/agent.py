import re
from typing import Any

from app.core.logging import audit_log
from app.graph.state import NewsState
from app.services.compliance_service import safe_evidence_snippet


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z]{3,}", (text or "").lower())
    return {token for token in tokens}


def _sentence_candidates(content: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", content or "") if part.strip()]


def _best_evidence_sentence(claim_tokens: set[str], article: dict[str, Any]) -> tuple[float, str]:
    best_score = 0.0
    best_sentence = ""
    for sentence in _sentence_candidates(article.get("content", ""))[:10]:
        sentence_tokens = _tokenize(sentence)
        if not sentence_tokens:
            continue
        overlap = len(claim_tokens.intersection(sentence_tokens))
        score = overlap / max(1, len(claim_tokens))
        if score > best_score:
            best_score = score
            best_sentence = sentence
    return best_score, best_sentence


def _verification_status(unique_sources: int) -> str:
    if unique_sources >= 3:
        return "verified"
    if unique_sources == 2:
        return "partially_verified"
    if unique_sources == 1:
        return "weakly_supported"
    return "unverified"


def verification_agent(state: NewsState):
    claims = state.get("claims", [])
    articles = state.get("articles", [])
    source_attribution = state.get("source_attribution", [])

    results = []
    for claim_item in claims:
        claim_text = claim_item.get("claim", "")
        claim_tokens = _tokenize(claim_text)
        if not claim_tokens:
            continue

        supporting_sources: dict[str, dict[str, Any]] = {}
        evidence = []
        for article in articles:
            score, sentence = _best_evidence_sentence(claim_tokens, article)
            if score < 0.28:
                continue

            source_name = (article.get("source") or "unknown").strip().lower()
            supporting_sources[source_name] = {
                "source": source_name,
                "url": article.get("url"),
                "published_at": article.get("published_at"),
            }
            evidence.append(
                {
                    "source": source_name,
                    "url": article.get("url"),
                    "published_at": article.get("published_at"),
                    "evidence_snippet": safe_evidence_snippet(sentence),
                    "match_score": round(score, 2),
                }
            )

        unique_sources = len(supporting_sources)
        status = _verification_status(unique_sources)
        confidence = round(min(0.98, unique_sources / 3), 2)

        results.append(
            {
                "claim_id": claim_item.get("claim_id"),
                "claim": claim_text,
                "type": claim_item.get("type", "fact"),
                "verification_status": status,
                "supporting_source_count": unique_sources,
                "required_sources": 3,
                "confidence": confidence,
                "evidence": evidence[:3],
            }
        )

    verification_lookup = {result["claim_id"]: result["verification_status"] for result in results}
    updated_attribution = []
    for source in source_attribution:
        status = "unverified"
        if results:
            supporting_hits = 0
            for item in results:
                supporting_sources = {entry.get("source") for entry in item.get("evidence", [])}
                if source.get("source") in supporting_sources:
                    supporting_hits += 1
            if supporting_hits > 0:
                status = "supported"
        updated_attribution.append({**source, "verification_status": status})

    result = {
        "verification_results": results,
        "verified": [result for result in results if result["verification_status"] == "verified"],
        "source_attribution": updated_attribution,
        "verification_lookup": verification_lookup,
    }
    audit_log(
        "agent_verification",
        {
            "claims_evaluated": len(results),
            "verified_claims": len(
                [item for item in results if item["verification_status"] == "verified"]
            ),
            "partially_verified_claims": len(
                [item for item in results if item["verification_status"] == "partially_verified"]
            ),
        },
    )
    return result
