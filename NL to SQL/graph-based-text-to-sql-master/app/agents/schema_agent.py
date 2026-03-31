import logging
import os
import json
from langchain_chroma import Chroma
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from app.config import embeddings, llm
from app.state.agent_state import GlobalState
from app.utils import extract_schema_from_db, BASE_DIR, DB_PATH

CHROMA_PATH = os.path.join(BASE_DIR, "chroma_schema_index")
_vectorstore = None


class SchemaSummary(BaseModel):
    key_tables: list[str] = Field(..., description="Most relevant tables")
    key_columns: list[str] = Field(..., description="Important columns")
    relationships: str = Field(..., description="Table relationships")
    summary_text: str = Field(..., description="Human-readable summary")


def build_schema_index(schema_docs):
    if not schema_docs:
        raise ValueError("No schema documents to index.")
    logging.info(f"Building Chroma index for {len(schema_docs)} schema docs...")
    vectorstore = Chroma.from_documents(
        documents=schema_docs,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )
    logging.info("Schema index built successfully.")
    return vectorstore


def extract_schema_from_metadata():
    """Extracts schema from schema_metadata.json for demo mode."""
    metadata_path = os.path.join(BASE_DIR, "app", "schema_metadata.json")
    with open(metadata_path, "r") as f:
        schema_metadata = json.load(f)

    docs = []
    for table_name, table_info in schema_metadata.items():
        description = table_info.get("description", "")
        columns = table_info.get("columns", {})
        relationships = table_info.get("relationships", {})

        schema_text = f"Table: {table_name}\nDescription: {description}\nColumns:\n"
        for col_name, col_desc in columns.items():
            schema_text += f"{col_name} - {col_desc}\n"

        if relationships:
            schema_text += "Relationships:\n"
            for fk, ref in relationships.items():
                schema_text += f"{fk} {ref}\n"

        docs.append(Document(
            page_content=schema_text,
            metadata={"source": table_name, "table_name": table_name}
        ))

    logging.info(f"✅ Extracted schema metadata for {len(docs)} tables")
    return docs


async def schema_agent_node(state: GlobalState) -> GlobalState:
    """Retrieves relevant schema using RAG and produces a structured schema summary."""
    global _vectorstore
    query = state.get("rewritten_query") or state.get("original_query")
    db_type = state.get("db_type", "sqlite").lower()

    if not query:
        raise ValueError("Missing rewritten_query or original_query in state")

    connection_config = state.get("connection_config", {})
    use_metadata = False

    if db_type != "sqlite":
        required_fields = ["database", "user", "password"]
        has_credentials = all(connection_config.get(field) for field in required_fields)
        if not has_credentials:
            use_metadata = True
            logging.info("🎭 Demo mode: Using schema metadata instead of live database")

    if _vectorstore is None:
        logging.info("Loading Chroma index...")
        try:
            _vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embeddings,
            )
            if _vectorstore._collection.count() == 0:
                raise ValueError("Empty index")
        except Exception:
            logging.warning("Rebuilding schema index...")
            # Always use schema_metadata.json — it covers all db types including SQLite
            schema_docs = extract_schema_from_metadata()
            _vectorstore = build_schema_index(schema_docs)

    from app.rag.schema_rag import expand_query_for_schema
    expanded_query = expand_query_for_schema(query)

    docs_with_scores = _vectorstore.similarity_search_with_score(expanded_query, k=5)

    query_lower = query.lower()

    # --- Distance threshold: tighter for simple queries, wider for multi-table ---
    aggregation_keywords = ["total", "sum", "revenue", "sales", "quantity sold", "how many", "count", "per category", "per month", "per product"]
    join_keywords = ["join", "ordered", "bought", "purchased", "with their", "and the"]

    if any(kw in query_lower for kw in join_keywords + aggregation_keywords):
        DISTANCE_THRESHOLD = 1.8
    else:
        DISTANCE_THRESHOLD = 1.2

    results = [doc for doc, score in docs_with_scores if score <= DISTANCE_THRESHOLD]
    if not results and docs_with_scores:
        results = [docs_with_scores[0][0]]

    logging.info(f"Scores: {[(doc.metadata.get('table_name'), round(score, 4)) for doc, score in docs_with_scores]}")
    logging.info(f"Kept {len(results)} tables after distance filtering (threshold={DISTANCE_THRESHOLD})")

    # --- Post-retrieval keyword filter: drop tables not relevant to the question ---
    def _is_table_needed(table_name: str, q: str) -> bool:
        """Return True only if the table is directly relevant to the query."""
        q = q.lower()
        rules = {
            "customers":  ["customer", "buyer", "client", "who bought", "who ordered", "user"],
            "employees":  ["employee", "staff", "sales rep", "salesperson", "handled", "department", "hired"],
            "categories": ["category", "categories", "product type", "product group", "per category"],
        }

        # orders is always needed for transactional queries
        if table_name == "orders":
            return True

        keywords = rules.get(table_name, [])
        return any(kw in q for kw in keywords)

    rag_docs = []
    relevant_tables = []

    for doc in results:
        table_name = doc.metadata.get("table_name") or doc.metadata.get("source") or "unknown"

        # Apply relevance filtering
        if _is_table_needed(table_name, query):
            relevant_tables.append(table_name)
            rag_docs.append(doc.page_content)

    # Normalize query once
    query_lower = query.lower()

    # --- Business-aware enhancement ---
    if "customer" in query_lower and "customers" not in relevant_tables:
        relevant_tables.append("customers")

    if (
        "employee" in query_lower
        or "employees" in query_lower
        or "who sold" in query_lower
        or "sales rep" in query_lower
    ) and "employees" not in relevant_tables:
        relevant_tables.append("employees")

    if "product" in query_lower and "products" not in relevant_tables:
        relevant_tables.append("products")

    # --- Relationship-aware fixes ---
    # Category queries need products as bridge
    if ("category" in query_lower or "categories" in query_lower) and "products" not in relevant_tables:
        relevant_tables.append("products")

    # Sales/revenue queries need products for price lookup
    if (
        "sale" in query_lower
        or "sales" in query_lower
        or "revenue" in query_lower
    ) and "products" not in relevant_tables:
        relevant_tables.append("products")

    # Ensure at least one table exists
    if not relevant_tables and results:
        first_doc = results[0]
        table_name = first_doc.metadata.get("table_name") or first_doc.metadata.get("source") or "unknown"
        relevant_tables.append(table_name)
        rag_docs.append(first_doc.page_content)

    # --- Add missing schema docs for tables forced in by rules ---
    all_schema_docs = extract_schema_from_metadata()
    schema_doc_map = {
        (doc.metadata.get("table_name") or doc.metadata.get("source")): doc.page_content
        for doc in all_schema_docs
    }

    for table in relevant_tables:
        if table in schema_doc_map and schema_doc_map[table] not in rag_docs:
            rag_docs.append(schema_doc_map[table])

# Ensure at least one table exists
    if not relevant_tables and results:
        first_doc = results[0]
        table_name = first_doc.metadata.get("table_name") or first_doc.metadata.get("source") or "unknown"
        relevant_tables.append(table_name)
        rag_docs.append(first_doc.page_content)

    schema_context = "\n".join(rag_docs)
    logging.info(f"Retrieved schema for tables: {relevant_tables}")

    parser = PydanticOutputParser(pydantic_object=SchemaSummary)
    prompt = ChatPromptTemplate.from_template(
        """You are a database schema expert.

User Query:
{query}

Relevant Schema:
{schema}

Extract:
- Key tables
- Key columns
- Relationships
- Short summary

{format_instructions}"""
    )

    chain = prompt | llm | parser
    try:
        structured = chain.invoke({
            "query": query,
            "schema": schema_context,
            "format_instructions": parser.get_format_instructions(),
        })
        structured_schema = structured.dict()
        schema_summary_text = structured.summary_text
    except Exception as e:
        logging.warning(f"LLM schema parsing failed: {e}")
        structured_schema = {
            "key_tables": relevant_tables,
            "key_columns": [],
            "relationships": "Auto-detected",
            "summary_text": f"Relevant tables: {', '.join(relevant_tables)}",
        }
        schema_summary_text = structured_schema["summary_text"]

    new_state = state.copy()
    new_state.update({
        "schema_context": schema_context,
        "relevant_tables": relevant_tables,
        "rag_docs": rag_docs,
        "schema_summary": schema_summary_text,
        "structured_schema": structured_schema,
        "status": "schema_retrieved",
    })

    logging.info("Schema Agent completed.")
    return new_state
