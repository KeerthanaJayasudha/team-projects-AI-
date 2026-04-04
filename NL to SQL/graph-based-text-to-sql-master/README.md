# 🧠 Text-to-SQL Multi-Agent System

A fully multi-agent LangGraph pipeline that converts natural language queries into SQL, executes them on a database, and returns structured results with natural language explanations — powered by FastAPI, LangChain, React, and Chroma (RAG).

## Overview

This project demonstrates how LLM agents can collaborate to perform complex reasoning and data querying tasks — from query understanding → SQL generation → validation → execution → visualization → natural language explanation.

Key highlights:

- Multi-agent pipeline using LangGraph with a shared `GlobalState`
- RAG-based schema retrieval via Chroma + HuggingFace embeddings (`all-MiniLM-L6-v2`)
- SQL generation with strict safety rules (read-only, no destructive queries)
- Multi-database support: SQLite, PostgreSQL, MySQL, SQL Server
- Demo/mock mode for PostgreSQL, MySQL, and SQL Server when credentials are not provided
- Natural language explanation of SQL results
- React frontend consuming a FastAPI REST backend

## Architecture

```
User Query
  └─► Query Rewriter
        └─► Schema Agent (RAG + Chroma)
              └─► SQL Generator (GPT-4o-mini)
                    └─► SQL Validator (sqlglot)
                          └─► Query Executor (SQLite / PG / MySQL / SQL Server)
                                └─► Visualization Agent
                                      └─► Explainability Agent
```

All agents share a `GlobalState` TypedDict — updated at each node and returned as a structured pipeline response.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, LangGraph, LangChain |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | Chroma |
| Frontend | React |
| Databases | SQLite, PostgreSQL, MySQL, SQL Server |
| Fake Data | Faker |

## Project Structure

```
app/
├── agents/          # LangGraph nodes (one file per agent)
├── api/             # FastAPI routes (/query endpoint)
├── db/              # DB executors (SQLite, Postgres, MySQL, SQL Server)
├── graph/           # LangGraph pipeline builder
├── rag/             # Chroma schema retrieval
├── state/           # GlobalState TypedDict
├── ui/              # Legacy Streamlit UI (replaced by React)
├── config.py        # LLM + embeddings config
├── main.py          # FastAPI app entry point
└── schema_metadata.json  # Table/column definitions for RAG

fakedb/
├── fakedata.py      # Generates fake SQLite DB using Faker
└── db_test.py       # Rebuilds the fake database

rebuild_schema_index.py  # Rebuilds Chroma vector index from schema_metadata.json
```

## Installation

```bash
git clone https://github.com/yourusername/graph-based-text-to-sql.git
cd graph-based-text-to-sql-master

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env` and set your API key:

```env
OPENAI_API_KEY=your_key_here
```

## Running the System

**1. Generate the fake database (first time only):**

```bash
python fakedb/fakedata.py
```

**2. Build the Chroma schema index (first time only):**

```bash
python rebuild_schema_index.py
```

**3. Start the FastAPI backend:**

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` — docs at `http://localhost:8000/docs`

**4. Start the React frontend:**

```bash
cd frontend   # or wherever your React app lives
npm install
npm run dev
```

## API Usage

`POST /query`

```json
{
  "query": "Show me the top 5 customers by number of orders",
  "session_id": "my-session",
  "db_type": "sqlite",
  "connection_config": {}
}
```

Response includes:

- `sql_query` — generated SQL
- `columns` / `rows` — query results
- `explanation` — natural language summary
- `validation_result` — SQL validation details
- `pipeline` — step-by-step trace of all agents
- `visualization` — chart/visualization hints

Supported `db_type` values: `sqlite`, `postgresql`, `mysql`, `sqlserver`

For PostgreSQL, MySQL, and SQL Server, pass credentials in `connection_config`:

```json
{
  "db_type": "postgresql",
  "connection_config": {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "postgres",
    "password": "secret"
  }
}
```

If credentials are missing or the driver is not installed, the system falls back to demo/mock data automatically.

## Rebuilding the Schema Index

If you update `schema_metadata.json` or change your database schema:

```bash
python rebuild_schema_index.py
```

Then restart the backend server.

## Safety Rules

The SQL generator enforces strict read-only behavior:

- Only `SELECT` queries are allowed
- `DELETE`, `DROP`, `UPDATE`, `INSERT` requests return `DELETE_BLOCKED`
- Column names are strictly mapped from the schema — no hallucinated columns
- Ambiguous column names across JOINs are always aliased

## Future Enhancements

- Multi-turn conversation memory
- Self-healing SQL via validator feedback loop
- Auto chart type suggestions in visualization agent
- Caching for repeated queries
- Support for more databases (BigQuery, Snowflake)

## License

MIT — free to use and modify.
