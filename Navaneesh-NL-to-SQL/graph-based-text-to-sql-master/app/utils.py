import os
import re
import sqlite3
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app", "text_db.sqlite")


def extract_schema_from_db(db_path: str):
    """Extracts SQLite schema and returns a list of LangChain Documents."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%';
    """).fetchall()

    docs = []
    if not tables:
        print("⚠️ No tables found in the database.")
        return docs

    for (table_name,) in tables:
        columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        if not columns:
            continue

        schema_text = f"Table: {table_name}\nDescription: Database table {table_name}\nColumns:\n"
        for col in columns:
            schema_text += f"{col[1]} - {col[2]}\n"

        fk_info = cursor.execute(f"PRAGMA foreign_key_list({table_name});").fetchall()
        if fk_info:
            schema_text += "Relationships:\n"
            for fk in fk_info:
                schema_text += f"{fk[3]} References {fk[2]}({fk[4]})\n"

        docs.append(Document(
            page_content=schema_text,
            metadata={"source": table_name, "table_name": table_name}
        ))

    conn.close()
    print(f"✅ Extracted schema for {len(docs)} tables.")
    return docs


def normalize_limit(sql: str, db_type: str) -> str:
    """Normalizes LIMIT/TOP syntax for the target database."""
    if db_type == "sqlserver":
        # SQLite/MySQL/Postgres LIMIT n → SQL Server TOP n
        match = re.search(r"limit\s+(\d+)", sql, re.IGNORECASE)
        if match:
            limit = match.group(1)
            sql = re.sub(r"limit\s+\d+", "", sql, flags=re.IGNORECASE)
            sql = re.sub(r"select", f"SELECT TOP {limit}", sql, count=1, flags=re.IGNORECASE)
    else:
        # SQL Server TOP n → LIMIT n (for SQLite, PostgreSQL, MySQL)
        match = re.search(r"SELECT\s+TOP\s+(\d+)", sql, re.IGNORECASE)
        if match:
            limit = match.group(1)
            sql = re.sub(r"TOP\s+\d+\s+", "", sql, flags=re.IGNORECASE)
            sql = sql.rstrip().rstrip(";") + f" LIMIT {limit};"
    return sql.strip()
