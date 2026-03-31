from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.graph.text_to_sql_graph import build_text_to_sql_graph

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: str = "demo_v2"
    db_type: Optional[str] = "sqlite"
    connection_config: Optional[Dict[str, Any]] = None


@router.post("/query")
async def query_endpoint(request: QueryRequest):
    try:
        graph = build_text_to_sql_graph()
        db_type = (request.db_type or "sqlite").lower().strip()

        import uuid
        thread_id = str(uuid.uuid4())

        state = {
            "original_query": request.query,
            "session_id": request.session_id,
            "db_type": db_type,
            "connection_config": request.connection_config or {}
        }

        async for event in graph.astream(
            state,
            config={"configurable": {"thread_id": thread_id}},
        ):
            if not isinstance(event, dict):
                continue
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    state.update(node_output)

        execution_result = state.get("execution_result", {})
        if not execution_result or not execution_result.get("success"):
            execution_result = {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time": 0,
                "error": execution_result.get("error", "Unknown error")
            }

        pipeline = []

        if state.get("rewritten_query"):
            pipeline.append({
                "stage": "Query Rewriter",
                "description": state.get("rewritten_query", ""),
                "explanation": state.get("rewrite_explanation", "")
            })

        if state.get("relevant_tables") or state.get("schema_summary"):
            tables_list = state.get("relevant_tables", [])
            tables_str = ", ".join(tables_list) if tables_list else "N/A"
            pipeline.append({
                "stage": "Schema Retrieval",
                "description": f"Relevant Tables: {tables_str}",
                "summary": state.get("schema_summary", "Schema retrieved successfully")
            })

        if state.get("sql_query"):
            cleaned = state.get("validation_result", {}).get("cleaned_sql") or state.get("sql_query", "")
            pipeline.append({
                "stage": "Query Generation",
                "description": cleaned
            })

        if state.get("validation_result"):
            validation_status = "✅ Valid" if state.get("validation_passed") else "⚠️ Issues Found"
            pipeline.append({
                "stage": "Validation",
                "description": validation_status,
                "details": state.get("validation_result", {})
            })

        if execution_result:
            exec_status = f"✅ Success - {execution_result.get('row_count', 0)} rows" if execution_result.get("success") else "❌ Failed"
            pipeline.append({
                "stage": "Query Execution",
                "description": exec_status,
                "execution_time": execution_result.get("execution_time", 0)
            })

        if state.get("explanation"):
            pipeline.append({
                "stage": "Natural Language Explanation",
                "description": state.get("explanation", "")
            })

        return {
            "columns": execution_result.get("columns", []),
            "rows": execution_result.get("rows", []),
            "results": execution_result.get("rows", []),
            "rewritten_query": state.get("rewritten_query", request.query),
            "rewrite_explanation": state.get("rewrite_explanation", ""),
            "schema_context": state.get("schema_context", ""),
            "relevant_tables": state.get("relevant_tables", []),
            "schema_summary": state.get("schema_summary", ""),
            "sql_query": state.get("sql_query", ""),
            "validation_result": state.get("validation_result", {}),
            "validation_passed": state.get("validation_passed", False),
            "execution_result": execution_result,
            "visualization": state.get("visualization", {}),
            "explanation": state.get("explanation", ""),
            "pipeline": pipeline
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
