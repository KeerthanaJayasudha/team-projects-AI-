def supervisor_agent(state: dict) -> dict:
    """
    Decides whether the query is:
    1. Schema/RAG question (no SQL needed)
    2. SQL analytical question
    """

    query = state.get("rewritten_query", "").lower()

    # Keywords that indicate schema/RAG intent
    rag_keywords = [
        "explain",
        "describe",
        "what is",
        "schema",
        "structure",
        "columns",
        "fields",
        "table",
        "meaning",
        "definition"
    ]

    # Decide route
    if any(keyword in query for keyword in rag_keywords):
        next_action = "schema_only"
    else:
        next_action = "sql_flow"

    state["next_action"] = next_action
    return state
