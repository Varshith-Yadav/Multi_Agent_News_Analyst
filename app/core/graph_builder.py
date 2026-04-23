from langgraph.graph import END, StateGraph

from app.agents.claims.agent import claims_agent
from app.agents.confidence.agent import confidence_agent
from app.agents.credibility.agent import credibility_agent
from app.agents.report_agent import report_agent
from app.agents.sentiment.agent import sentiment_agent
from app.agents.sourcing.agent import sourcing_agent
from app.agents.summarization.agent import summarize_agent
from app.agents.trends.agent import trends_agent
from app.agents.verification.agent import verification_agent
from app.graph.state import NewsState


def build_graph():
    graph = StateGraph(NewsState)

    graph.add_node("sourcing", sourcing_agent)
    graph.add_node("summarize", summarize_agent)
    graph.add_node("sentiment", sentiment_agent)
    graph.add_node("trends", trends_agent)
    graph.add_node("credibility", credibility_agent)
    graph.add_node("claims", claims_agent)
    graph.add_node("verify", verification_agent)
    graph.add_node("confidence", confidence_agent)
    graph.add_node("report", report_agent)

    graph.set_entry_point("sourcing")
    graph.add_edge("sourcing", "summarize")
    graph.add_edge("summarize", "sentiment")
    graph.add_edge("sentiment", "trends")
    graph.add_edge("trends", "credibility")
    graph.add_edge("credibility", "claims")
    graph.add_edge("claims", "verify")
    graph.add_edge("verify", "confidence")
    graph.add_edge("confidence", "report")
    graph.add_edge("report", END)

    return graph.compile()
