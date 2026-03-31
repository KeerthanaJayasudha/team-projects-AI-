import logging
from app.db.base_executor import BaseExecutor
from app.db.sql_executors import (
    SQLiteExecutor,
    PostgresExecutor,
    MySQLExecutor,
    SQLServerExecutor
)


def get_executor(db_type: str) -> BaseExecutor:
    """
    Factory function to get appropriate database executor.
    
    Args:
        db_type: Database type (sqlite, postgresql, mysql, sqlserver)
        
    Returns:
        BaseExecutor instance for the specified database type
    """
    # Normalize to lowercase
    db_type_normalized = db_type.lower().strip() if db_type else "sqlite"
    
    executor_map = {
        "sqlite": SQLiteExecutor,
        "postgresql": PostgresExecutor,
        "postgres": PostgresExecutor,  # alias
        "mysql": MySQLExecutor,
        "sqlserver": SQLServerExecutor,
        "mssql": SQLServerExecutor,  # alias
    }
    
    executor_class = executor_map.get(db_type_normalized)
    
    if executor_class is None:
        logging.warning(f"Unknown db_type '{db_type}', defaulting to SQLite")
        executor_class = SQLiteExecutor
    
    return executor_class()
