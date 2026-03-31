from typing import TypedDict, Optional, Any, Dict, List


class GlobalState(TypedDict, total=False):
    # Input
    original_query: str
    session_id: str

    # Rewriter
    rewritten_query: str
    rewrite_explanation: str
    rewrite_metadata: Dict[str, Any]
    rewrite_history: List[Dict[str, Any]]

    # Schema
    schema_context: str  # Changed from Dict to str (it's the schema text)
    relevant_tables: List[str]
    rag_docs: List[str]
    schema_summary: str
    structured_schema: Dict[str, Any]

    # SQL generation
    sql_query: str

    # Validation
    validation_result: Dict[str, Any]
    validation_passed: bool
    validation_explanation: str
    validation_history: List[Dict[str, Any]]

    # Execution
    execution_result: Dict[str, Any]
    execution_history: List[Dict[str, Any]]

    # Visualization
    visualization: Dict[str, Any]
    visual_assets: Dict[str, Any]

    # Explainability
    explanation: str
    natural_language_explanation: str
    explanation_history: List[Dict[str, Any]]

    # Status tracking
    status: str
    
    # Pipeline tracking
    pipeline: List[Dict[str, str]]
    
    # Database configuration
    db_type: str
    connection_config: Dict[str, Any]
