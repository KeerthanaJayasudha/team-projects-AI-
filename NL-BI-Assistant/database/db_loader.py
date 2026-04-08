# utils/db_loader.py
# Convenience helper for loading a specific table via the default connection.
# Separates "get a connection" (db_connector) from "load data" (db_loader).

import logging
from .db_connector import get_default_engine
from services.db_service import load_table, get_tables

logger = logging.getLogger(__name__)


def load_default_table(table_name: str):
    """
    Connect using default env credentials and load the specified table.

    Returns a normalised DataFrame, or None on failure.
    """
    engine = get_default_engine()

    if engine is None:
        logger.error("Could not establish default DB connection.")
        return None

    available = get_tables(engine)

    if table_name not in available:
        logger.error(
            "Table '%s' not found. Available tables: %s", table_name, available
        )
        return None

    return load_table(engine, table_name)


def list_default_tables() -> list[str]:
    """
    Return table names from the default database connection.
    """
    engine = get_default_engine()

    if engine is None:
        return []

    return get_tables(engine)