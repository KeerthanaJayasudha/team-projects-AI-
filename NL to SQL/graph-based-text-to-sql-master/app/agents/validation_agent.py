import logging
import re
from datetime import datetime
from app.state.agent_state import GlobalState


async def validation_node(state: GlobalState) -> GlobalState:
    """
    Validation Agent (Optimized for Speed):
    ✅ Cleans and validates SQL.
    ✅ Ensures it's read-only (security check only).
    ✅ Skips syntax validation for immediate response.
    """

    sql_query = (state.get("sql_query") or "").strip()
    if not sql_query:
        raise ValueError("No SQL found in state to validate")

    logging.info("🧩 Validating generated SQL for safety...")

    # --- 1️⃣ Clean minor noise (LLM leftovers) ---
    sql_query = re.sub(r"```(?:sql)?|```", "", sql_query).strip()
    sql_query = re.sub(r"^\{+|\}+$", "", sql_query).strip()

    # --- 2️⃣ Check if LLM flagged a destructive query ---
    if sql_query.strip().upper() == "DELETE_BLOCKED":
        explanation = "❌ Destructive operation requested (DELETE/DROP/UPDATE/INSERT). Only SELECT queries are allowed."
        logging.warning(explanation)
        new_state = state.copy()
        new_state.update({
            "validation_passed": False,
            "validation_result": {"passed": False, "explanation": explanation, "cleaned_sql": ""},
            "validation_explanation": explanation,
            "status": "validation_failed"
        })
        return new_state

    # --- 1️⃣ Clean minor noise (LLM leftovers) ---
    sql_query = re.sub(r"```(?:sql)?|```", "", sql_query).strip()
    sql_query = re.sub(r"^\{+|\}+$", "", sql_query).strip()

    # --- 2️⃣ Security Validation (read-only enforcement) ---
    forbidden_keywords = ["delete", "drop", "update", "insert", "alter", "truncate"]
    lower_sql = sql_query.lower()

    for keyword in forbidden_keywords:
        if re.search(rf"\b{keyword}\b", lower_sql):
            explanation = f"❌ Unsafe SQL detected (contains '{keyword.upper()}'). Only SELECT queries are allowed."
            logging.warning(explanation)
            new_state = state.copy()
            new_state.update({
                "validation_passed": False,
                "validation_explanation": explanation,
                "status": "validation_failed"
            })
            return new_state

    if not lower_sql.startswith("select"):
        explanation = "❌ Only SELECT statements are permitted. This query is not read-only."
        logging.warning(explanation)
        new_state = state.copy()
        new_state.update({
            "validation_passed": False,
            "validation_explanation": explanation,
            "status": "validation_failed"
        })
        return new_state

    # --- 3️⃣ Syntax Validation (OPTIMIZED - Skip for immediate response) ---
    # Skip EXPLAIN query to reduce latency
    validation_passed = True
    explanation = "✅ SQL security validated (read-only check passed)."

    # --- 4️⃣ Record History ---
    validation_history = state.get("validation_history", [])
    validation_history.append({
        "time": datetime.utcnow().isoformat(),
        "sql": sql_query,
        "passed": validation_passed,
        "explanation": explanation
    })

    # --- 5️⃣ Update Global State ---
    new_state = state.copy()
    new_state.update({
        "sql_query": sql_query,
        "validation_result": {
            "passed": validation_passed,
            "explanation": explanation,
            "cleaned_sql": sql_query
        },
        "validation_passed": validation_passed,
        "validation_explanation": explanation,
        "validation_history": validation_history,
        "status": "validated" if validation_passed else "validation_failed"
    })

    if validation_passed:
        logging.info("✅ SQL validation passed.")
    else:
        logging.warning("⚠️ SQL validation failed.")

    return new_state
