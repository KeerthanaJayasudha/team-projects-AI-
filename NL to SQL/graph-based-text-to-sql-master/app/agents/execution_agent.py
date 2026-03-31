import logging
from datetime import datetime

from app.state.agent_state import GlobalState
from app.utils import DB_PATH
from app.db.factory import get_executor
from app.utils import normalize_limit


async def query_execution_node(state: GlobalState) -> GlobalState:
    """Runs validated SQL against the database and updates GlobalState with results."""
    sql_query = state.get("sql_query", "")
    db_type = (state.get("db_type", "sqlite") or "sqlite").lower().strip()
    sql_query = normalize_limit(sql_query, db_type)

    if not sql_query:
        logging.warning("No SQL query found, using safe fallback")
        sql_query = "SELECT 1;"

    connection_config = state.get("connection_config") or {}
    if db_type == "sqlite" and not connection_config.get("db_path"):
        connection_config["db_path"] = DB_PATH

    logging.info(f"🚀 Executing SQL on {db_type.upper()}: {sql_query}")

    executor = get_executor(db_type)
    try:
        result = executor.execute(sql_query, connection_config)
    except Exception as e:
        logging.error(f"Execution error: {e}")
        result = {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time": 0,
            "error": str(e)
        }

    execution_history = state.get("execution_history", [])
    execution_history.append({
        "time": datetime.utcnow().isoformat(),
        "query": sql_query,
        "db_type": db_type,
        "success": result.get("success", False),
        "row_count": result.get("row_count", 0),
        "execution_time": result.get("execution_time", 0),
        "error": result.get("error")
    })

    new_state = state.copy()
    new_state.update({
        "execution_result": result,
        "execution_history": execution_history,
        "status": "query_executed" if result["success"] else "execution_failed"
    })

    if result["success"]:
        logging.info(f"✅ Query executed successfully — {result.get('row_count',0)} rows in {result.get('execution_time',0)}s")
    else:
        logging.warning(f"⚠️ Query execution failed: {result.get('error')}")

    return new_state
