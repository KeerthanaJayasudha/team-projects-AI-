import json
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.config import llm


def expand_query_for_schema(query: str) -> str:
    """Expands the user query with relevant database keywords for better schema retrieval."""
    expansion_prompt = f"""Given this database query, identify ONLY the tables and columns that are DIRECTLY needed.

Query: "{query}"

Available tables:
- customers: customer_id, name, email, country
- products: product_id, name, category_id, price
- orders: order_id, customer_id, product_id, employee_id, quantity, order_date
- employees: employee_id, name, department, hire_date
- categories: category_id, category_name, description

Rules:
1. If query mentions "customer name/email/info/country" → customers
2. If query mentions "orders/purchases/bought/sales/quantity/order date/monthly/revenue" → orders (+ customers or products if needed)
3. If query mentions "product name/price/catalog" → products
4. If query mentions "category/categories/product type/group by category" → categories (+ products if needed)
5. If query mentions "employee/sales rep/staff/who handled/department" → employees (+ orders if performance needed)
6. Be MINIMAL — only include tables directly referenced

Return format: table_name column_name keywords (space separated, no commas)

Examples:
Query: "Show customer name and email"
Output: customers name email

Query: "List all orders with product names"
Output: orders products order_id product_id name quantity order_date

Query: "Which category has the most sales"
Output: categories products orders category_id category_name quantity sales

Query: "Top employees by number of orders handled"
Output: employees orders employee_id name department order_id

Query: "Monthly revenue trend"
Output: orders products order_date quantity price revenue monthly

Now analyze the query above:"""

    try:
        response = llm.invoke(expansion_prompt)
        expanded_keywords = response.content.strip()
        expanded_query = f"{query} {expanded_keywords}"
        logging.info(f"Expanded query for schema retrieval: {expanded_query}")
        return expanded_query
    except Exception as e:
        logging.warning(f"Query expansion failed: {e}, using original query")
        return query


def build_schema_index():
    """Builds Chroma vector index from schema metadata with enriched content."""
    with open("app/schema_metadata.json") as f:
        schema = json.load(f)

    docs = []
    for table, info in schema.items():
        text = f"Table: {table}\nDescription: {info['description']}\nColumns:\n"
        for col, desc in info["columns"].items():
            text += f"{col} - {desc}\n"
        if "relationships" in info and info["relationships"]:
            text += "Relationships:\n"
            for fk, ref in info["relationships"].items():
                text += f"{fk} {ref}\n"
        docs.append(Document(
            page_content=text,
            metadata={"source": table, "table_name": table}
        ))

    embeddings = OpenAIEmbeddings()
    vectordb = Chroma.from_documents(docs, embeddings, persist_directory="chroma_schema_index")
    logging.info(f"Built schema index with {len(docs)} tables")
    return vectordb
