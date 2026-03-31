from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.sql_executors import init_sqlite_db
from app.utils import DB_PATH

# Seed the demo database on startup (no-op if already populated)
init_sqlite_db(DB_PATH)

app = FastAPI(
    title="Text-to-SQL API",
    description="Multi-database Text-to-SQL conversion API with dynamic executor support",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Text-to-SQL API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query (POST)",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "supported_databases": ["sqlite", "postgresql", "mysql", "sqlserver"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(router)
