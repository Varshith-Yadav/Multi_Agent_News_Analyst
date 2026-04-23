from langgraph.graph import StateGraph

from app.graph.state import NewsState

from app.agents.sourcing import sourcing_agent
from app.agents.summarization import summarization_agent
from app.agents.sentiment import sentiment_agent
from app.agents.trends import trends_agent

from app.agents.credibility  import credibility_agent
from app.agents.claims import claims_agent
from app.agents.verification import verification_agent


def build_graph():
    graph = StateGraph(NewsState)

    # Nodes
    graph.add_node("sourcing", sourcing_agent)
    graph.add_node("summarize", summarization_agent)
    graph.add_node("sentiment", sentiment_agent)
    graph.add_node("trends", trends_agent)

    graph.add_node("credibility", credibility_agent)
    graph.add_node("claims", claims_agent)
    graph.add_node("verify", verification_agent)

    # Flow
    graph.set_entry_point("sourcing")

    graph.add_edge("sourcing", "summarize")

    # Parallel layer 1
    graph.add_edge("summarize", "sentiment")
    graph.add_edge("summarize", "trends")
    graph.add_edge("summarize", "claims")

    # Parallel layer 2
    graph.add_edge("sourcing", "credibility")

    # Verification depends on claims
    graph.add_edge("claims", "verify")

    graph.set_finish_point("verify")

    return graph.compile()