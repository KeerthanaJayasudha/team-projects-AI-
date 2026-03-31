import logging
from langchain_core.prompts import ChatPromptTemplate
from app.config import llm
from app.state.agent_state import GlobalState


prompt = ChatPromptTemplate.from_template(
"""
You are an expert SQL generator.

STRICT RULES:
1. Use ONLY tables listed in the schema below
2. Use ONLY columns listed in the schema below
3. Do NOT invent or create new column names
4. If the user asks for 'customer name', map it to the exact column from schema (e.g., 'name')
5. If a requested column does not exist, choose the closest matching column from the schema
6. Return ONLY a valid SQL query
7. Do NOT use SELECT *
8. Only generate read-only queries (SELECT)
9. If the user asks to DELETE, DROP, UPDATE, INSERT, or any destructive operation — return exactly: DELETE_BLOCKED
10. Do NOT convert destructive requests into SELECT queries

User Query:
{query}

Relevant Schema:
{schema}

Target Database: {db_type}

Database-Specific Syntax Rules:
- SQLite: Use "LIMIT n" at the end of the query for row limits. NEVER use TOP.
- PostgreSQL: Use "LIMIT n" at the end of the query for row limits. NEVER use TOP.
- MySQL: Use "LIMIT n" at the end of the query for row limits. NEVER use TOP.
- SQL Server: Use "SELECT TOP n" immediately after SELECT for row limits. NEVER use LIMIT.

SQL Generation Rules:
- Use correct JOINs when multiple tables are required
- Use aggregation functions when the query asks for totals, averages, counts, etc.
- Always include GROUP BY when aggregation is used
- Return meaningful column aliases for aggregated results
- Only return the columns needed to answer the query
- Prefer human-readable business columns over raw IDs when available
- If the query is about customers, prefer joining the customers table and returning customers.name instead of only customer_id
- If the query is about employees, prefer joining the employees table and returning employees.name instead of only employee_id
- If the query is about products, prefer joining the products table and returning products.name instead of only product_id
- Only return raw IDs alone if the user explicitly asks for IDs
- For ranking queries like "top customers", "top employees", or "top products", return the entity name whenever the schema provides it

CRITICAL: Map user terms to exact schema columns:
- "customer name" → use the exact column name from schema (e.g., "name")
- "customer email" → use the exact column name from schema (e.g., "email")
- "product name" → use the exact column name from schema (e.g., "name")
- Never create columns like "customer_name" if schema only has "name"
- When the same column name (e.g., "name") exists in multiple tables in a JOIN, ALWAYS use aliases:
  Example: customers.name AS customer_name, products.name AS product_name
- Never select two columns with the same output name without aliasing them

Generate a valid SQL query compatible with {db_type}.

Return ONLY the SQL query.
No explanations.
No markdown.
No code blocks.
"""
)


async def query_generation_node(state: GlobalState) -> GlobalState:
    """Generate SQL from rewritten query + schema context."""

    query = state.get("rewritten_query") or state.get("original_query")
    schema = state.get("schema_context", "")
    db_type = state.get("db_type", "sqlite").upper()

    if not query:
        raise ValueError("Missing query for SQL generation")

    logging.info(f"🧠 Generating SQL query for {db_type}...")

    try:
        chain = prompt | llm
        result = await chain.ainvoke({
            "query": query,
            "schema": schema,
            "db_type": db_type,
        })

        sql = result.content.strip()

        # Basic safety fallback
        if not sql:
            raise ValueError("Empty SQL generated")

    except Exception as e:
        logging.error(f"SQL generation failed: {e}")
        sql = "SELECT 1;"  # safe fallback

    new_state = state.copy()
    new_state.update({
        "sql_query": sql,
        "status": "sql_generated"
    })

    logging.info(f"✅ SQL generated: {sql}")
    return new_state
