from app.core.llm import call_llm_json
from app.core.logging import audit_log
from app.schemas.agent_outputs import SentimentOutput


def sentiment_agent(state):
    text = state.get("summary", "")

    prompt = f"""
Analyze sentiment.

Return JSON:
{{
    "sentiment": "positive/negative/neutral",
    "confidence": 0-1
}}

Text:
{text}
"""

    try:
        data = call_llm_json(prompt)
        if not isinstance(data, dict):
            raise ValueError("Sentiment response was not a JSON object")
        validated = SentimentOutput(**data)
    except Exception:
        validated = SentimentOutput(sentiment="neutral", confidence=0.5)

    result = {
        "sentiment": validated.sentiment.lower(),
        "sentiment_conf": validated.confidence,
    }
    audit_log("agent_sentiment", result)
    return result
