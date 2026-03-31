import logging
from datetime import datetime

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.state.agent_state import GlobalState
from app.config import llm


# ------------------------------------------------------------
# 🧩 Define structured output model
# ------------------------------------------------------------
class QueryRewriteOutput(BaseModel):
    rewritten_query: str = Field(..., description="Rewritten SQL-friendly version of the query.")
    explanation: str = Field(..., description="Explanation of how and why the query was rewritten.")
    metadata: dict = Field(default_factory=dict, description="Optional metadata or notes.")


# ------------------------------------------------------------
# 🧠 Define prompt
# ------------------------------------------------------------
rewriter_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a minimal query rewriter for a Text-to-SQL assistant.

Your task is to restate the user's question in a clear, SQL-friendly way WITHOUT changing its meaning.

CRITICAL RULES:
1. PRESERVE all user specifications: limits (top 3, first 5), filters, conditions, aggregations
2. If user says "show all X" → Keep it as-is, DO NOT add filters
3. If user says "top N" or "first N" → PRESERVE the number N
4. NEVER add WHERE, HAVING, GROUP BY, or conditions unless in original query
5. NEVER infer thresholds or filters not mentioned by user
6. Only rephrase for clarity, NEVER for "optimization"
7. If query is already clear, return it UNCHANGED

Examples:
- "show all customers" → "show all customers" (NO CHANGE)
- "show top 3 customers" → "show top 3 customers" (PRESERVE LIMIT)
- "first 5 products" → "first 5 products" (PRESERVE LIMIT)
- "list products" → "list products" (NO CHANGE)
- "customers who ordered more than 5 times" → "customers who ordered more than 5 times" (keep filter)

Respond ONLY in structured JSON as instructed below.

{format_instructions}
"""
    ),
    (
        "human",
        "Original user question: \"{query}\""
    ),
])

# ------------------------------------------------------------
# 🚀 Query Rewriter Node
# ------------------------------------------------------------
async def query_rewriter_node(state: GlobalState) -> GlobalState:
    """Query Rewriter Agent (optimized for speed)."""
    query = state.get("original_query", "").strip()
    if not query:
        raise ValueError("Missing 'original_query' in GlobalState")

    logging.info("🔍 Checking if query needs rewriting...")

    # Skip LLM call for simple queries (optimization for speed)
    simple_patterns = ["show", "list", "get", "find", "top", "first", "all"]
    is_simple = any(pattern in query.lower() for pattern in simple_patterns)
    
    if is_simple and len(query.split()) <= 6:
        # Skip rewriting for simple queries
        logging.info(f"✅ Query is simple, skipping rewrite: {query}")
        new_state = state.copy()
        new_state.update({
            "rewritten_query": query,
            "rewrite_explanation": "Simple query - no rewriting needed",
            "rewrite_metadata": {"skipped": True},
            "rewrite_history": [],
            "status": "query_rewritten",
        })
        return new_state

    # For complex queries, use LLM
    logging.info("🔍 Rewriting complex query...")
    parser = PydanticOutputParser(pydantic_object=QueryRewriteOutput)
    chain = rewriter_prompt | llm | parser

    try:
        result: QueryRewriteOutput = await chain.ainvoke({
            "query": query,
            "format_instructions": parser.get_format_instructions(),
        })
    except Exception as e:
        logging.error(f"⚠️ Parsing or LLM error: {e}")
        result = QueryRewriteOutput(
            rewritten_query=query,
            explanation=f"Parser failed — returning original query. ({e})",
            metadata={}
        )

    # Update history
    history = state.get("rewrite_history", [])
    history.append({
        "time": datetime.utcnow().isoformat(),
        "model": getattr(llm, "model", "unknown"),
        "input": query,
        "output": result.rewritten_query,
        "explanation": result.explanation,
        "metadata": result.metadata,
    })

    # Build new state
    new_state = state.copy()
    new_state.update({
        "rewritten_query": result.rewritten_query,
        "rewrite_explanation": result.explanation,
        "rewrite_metadata": result.metadata,
        "rewrite_history": history,
        "status": "query_rewritten",
    })

    logging.info(f"✅ Query rewritten: {result.rewritten_query}")
    return new_state
