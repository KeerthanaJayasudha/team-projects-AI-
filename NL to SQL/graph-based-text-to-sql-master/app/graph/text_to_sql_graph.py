import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from app.agents.query_rewriter_agent import query_rewriter_node
from app.agents.schema_agent import schema_agent_node
from app.agents.query_generation_agent import query_generation_node
from app.agents.validation_agent import validation_node
from app.agents.execution_agent import query_execution_node
from app.agents.visualization_agent import visualization_node
from app.agents.explainability_agent import explainability_node
from app.state.agent_state import GlobalState


def build_text_to_sql_graph():
    """Builds and returns the compiled LangGraph Text-to-SQL pipeline."""
    logging.info("Building Text-to-SQL workflow graph...")

    graph = StateGraph(GlobalState)

    graph.add_node("query_rewriter_node", query_rewriter_node)
    graph.add_node("schema_agent_node", schema_agent_node)
    graph.add_node("query_generation_node", query_generation_node)
    graph.add_node("validation_node", validation_node)
    graph.add_node("query_execution_node", query_execution_node)
    graph.add_node("visualization_node", visualization_node)
    graph.add_node("explainability_node", explainability_node)

    graph.set_entry_point("query_rewriter_node")
    graph.add_edge("query_rewriter_node", "schema_agent_node")
    graph.add_edge("schema_agent_node", "query_generation_node")
    graph.add_edge("query_generation_node", "validation_node")
    graph.add_edge("validation_node", "query_execution_node")
    graph.add_edge("query_execution_node", "visualization_node")
    graph.add_edge("visualization_node", "explainability_node")
    graph.add_edge("explainability_node", END)

    memory = MemorySaver()
    compiled_graph = graph.compile(checkpointer=memory)

    logging.info("✅ Text-to-SQL workflow graph built successfully.")
    return compiled_graph
