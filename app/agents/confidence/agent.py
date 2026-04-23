from app.core.logging import audit_log


def confidence_agent(state):
    credibility = float(state.get("credibility_score", 0.5) or 0.5)
    sentiment_conf = float(state.get("sentiment_conf", 0.5) or 0.5)
    verification_results = state.get("verification_results", [])
    verified_claims = [
        item for item in verification_results if item.get("verification_status") == "verified"
    ]
    partially_verified_claims = [
        item for item in verification_results if item.get("verification_status") == "partially_verified"
    ]
    total_claims = max(1, len(state.get("claims", [])))

    verified_ratio = (len(verified_claims) + (0.5 * len(partially_verified_claims))) / total_claims

    final_score = (
        0.45 * credibility +
        0.3 * verified_ratio +
        0.25 * sentiment_conf
    )

    result = {"confidence_score": round(final_score, 2)}
    audit_log(
        "agent_confidence",
        {
            "credibility_component": credibility,
            "verification_component": round(verified_ratio, 2),
            "sentiment_component": sentiment_conf,
            "confidence_score": result["confidence_score"],
        },
    )
    return result
