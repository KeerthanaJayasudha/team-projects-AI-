import logging
from datetime import datetime

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.config import llm
from app.state.agent_state import GlobalState


# ------------------------------------------------------------
# Structured Output Schema
# ------------------------------------------------------------
class ExplanationOutput(BaseModel):
    summary: str = Field(..., description="Concise explanation for the user.")


# ------------------------------------------------------------
# Explainability Node
# ------------------------------------------------------------
async def explainability_node(state: GlobalState) -> GlobalState:
    """
    Explainability Agent:
    Handles two modes:
    1. SQL result explanation
    2. Schema/table explanation (RAG-only mode)
    """

    sql_query = state.get("sql_query") or state.get("validated_sql") or state.get("generated_sql")
    execution_result = state.get("execution_result", {})
    schema_context = state.get("schema_context", "")

    logging.info("🧠 Generating explanation...")

    parser = PydanticOutputParser(pydantic_object=ExplanationOutput)

    # ------------------------------------------------------------
    # Mode 1: SQL explanation
    # ------------------------------------------------------------
    if sql_query and execution_result:
        all_rows = execution_result.get("rows", [])
        row_count = execution_result.get("row_count", len(all_rows))
        # Pass all rows (capped at 10 to stay within token limits)
        sample_rows = all_rows[:10]

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a data analyst. Explain the SQL result in one short sentence.\n"
                "IMPORTANT: The result contains exactly {row_count} rows. "
                "Your explanation MUST reflect this exact count and the actual top values shown. "
                "Do not describe fewer rows than were returned.\n{format_instructions}",
            ),
            (
                "human",
                "SQL:\n{sql_query}\n\nTotal rows returned: {row_count}\nResults:\n{sample_rows}",
            ),
        ])

        chain = prompt | llm | parser

        result = await chain.ainvoke({
            "sql_query": sql_query,
            "sample_rows": sample_rows,
            "row_count": row_count,
            "format_instructions": parser.get_format_instructions(),
        })

        explanation_text = result.summary

    # ------------------------------------------------------------
    # Mode 2: RAG-only schema explanation
    # ------------------------------------------------------------
    else:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a database expert. Explain the table or schema in one concise sentence.\n{format_instructions}",
            ),
            (
                "human",
                "Schema context:\n{schema_context}",
            ),
        ])

        chain = prompt | llm | parser

        result = await chain.ainvoke({
            "schema_context": schema_context,
            "format_instructions": parser.get_format_instructions(),
        })

        explanation_text = result.summary

    # ---- Record History ----
    explanation_history = state.get("explanation_history", [])
    explanation_history.append({
        "time": datetime.utcnow().isoformat(),
        "explanation": explanation_text
    })

    # ---- Update GlobalState ----
    new_state = state.copy()
    new_state.update({
        "explanation": explanation_text,
        "natural_language_explanation": explanation_text,
        "explanation_history": explanation_history,
        "status": "explained"
    })

    logging.info("✅ Explanation generated successfully.")
    return new_state
