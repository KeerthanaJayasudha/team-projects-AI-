import time
import logging
import sqlite3
import os
from typing import Dict, Any, Optional, List
from app.db.base_executor import BaseExecutor


def init_sqlite_db(db_path: str = "app/text_db.sqlite") -> None:
    """
    Initialize the SQLite demo database from fixed seed data (5 tables).
    Idempotent — only seeds if the database is empty. Safe to call on every startup.
    """
    from app.db.seed_data import CATEGORIES, EMPLOYEES, CUSTOMERS, PRODUCTS, ORDERS

    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id   INTEGER PRIMARY KEY,
            category_name TEXT,
            description   TEXT
        );
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            name        TEXT,
            department  TEXT,
            hire_date   TEXT
        );
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name        TEXT,
            email       TEXT,
            country     TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
            product_id  INTEGER PRIMARY KEY,
            name        TEXT,
            category_id INTEGER,
            price       REAL,
            FOREIGN KEY(category_id) REFERENCES categories(category_id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id    INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id  INTEGER,
            employee_id INTEGER,
            quantity    INTEGER,
            order_date  TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(product_id)  REFERENCES products(product_id),
            FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
        );
    """)

    # Only seed if tables are empty
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO categories (category_id, category_name, description) VALUES (?,?,?)",
            CATEGORIES
        )
        cur.executemany(
            "INSERT INTO employees (employee_id, name, department, hire_date) VALUES (?,?,?,?)",
            EMPLOYEES
        )
        cur.executemany(
            "INSERT INTO customers (customer_id, name, email, country) VALUES (?,?,?,?)",
            CUSTOMERS
        )
        cur.executemany(
            "INSERT INTO products (product_id, name, category_id, price) VALUES (?,?,?,?)",
            PRODUCTS
        )
        cur.executemany(
            "INSERT INTO orders (order_id, customer_id, product_id, employee_id, quantity, order_date) VALUES (?,?,?,?,?,?)",
            ORDERS
        )
        logging.info("✅ SQLite demo database seeded with fixed sample data (5 tables).")
    else:
        logging.info("✅ SQLite demo database already populated — reusing existing data.")

    conn.commit()
    conn.close()


def generate_mock_data(query: str) -> Dict[str, Any]:
    """
    Demo mode fallback for non-SQLite databases without credentials.
    Executes the query against the local SQLite demo database.
    Normalizes SQL Server TOP n syntax to SQLite LIMIT n before execution.
    """
    import re
    from app.utils import DB_PATH
    logging.info("🎭 Demo mode: routing query to SQLite demo database")

    # Normalize TOP n → LIMIT n so SQLite can execute SQL Server-style queries
    top_match = re.search(r"\bTOP\s+(\d+)\b", query, re.IGNORECASE)
    if top_match:
        n = top_match.group(1)
        query = re.sub(r"\bTOP\s+\d+\b\s*", "", query, flags=re.IGNORECASE)
        query = query.rstrip().rstrip(";") + f" LIMIT {n}"
        logging.info(f"🔧 Demo fallback: rewrote TOP {n} → LIMIT {n} for SQLite execution")

    executor = SQLiteExecutor()
    return executor.execute(query, {"db_path": DB_PATH})

class SQLiteExecutor(BaseExecutor):
    """SQLite database executor."""
    
    def execute(self, query: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query on SQLite database."""
        import sqlite3
        
        db_path = connection_config.get("db_path", "app/text_db.sqlite")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            start = time.time()
            cursor.execute(query)
            rows = cursor.fetchall()
            execution_time = round(time.time() - start, 4)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = [dict(row) for row in rows]
            
            conn.close()
            
            return {
                "success": True,
                "columns": columns,
                "rows": result,
                "row_count": len(result),
                "execution_time": execution_time,
                "error": None
            }
            
        except Exception as e:
            logging.error(f"⚠️ SQLite execution failed: {e}")
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time": 0,
                "error": str(e)
            }


class PostgresExecutor(BaseExecutor):
    """PostgreSQL database executor with demo mode support."""
    
    @staticmethod
    def _validate_config(connection_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate PostgreSQL connection configuration.
        
        Returns:
            Tuple of (is_valid, missing_field)
        """
        required_fields = ["database", "user", "password"]
        for field in required_fields:
            if not connection_config.get(field):
                return False, field
        return True, None
    
    def execute(self, query: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query on PostgreSQL database or return mock data in demo mode."""
        # Validate configuration
        is_valid, missing_field = self._validate_config(connection_config)
        
        if not is_valid:
            logging.info(f"🎭 PostgreSQL demo mode: missing '{missing_field}' - returning mock data")
            return generate_mock_data(query)
        
        # Check if psycopg2 is installed
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            logging.info("🎭 PostgreSQL demo mode: psycopg2 not installed - returning mock data")
            return generate_mock_data(query)
        
        try:
            conn = psycopg2.connect(
                host=connection_config.get("host", "localhost"),
                port=connection_config.get("port", 5432),
                database=connection_config.get("database"),
                user=connection_config.get("user"),
                password=connection_config.get("password")
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            start = time.time()
            cursor.execute(query)
            rows = cursor.fetchall()
            execution_time = round(time.time() - start, 4)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = [dict(row) for row in rows]
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "columns": columns,
                "rows": result,
                "row_count": len(result),
                "execution_time": execution_time,
                "error": None
            }
            
        except Exception as e:
            logging.warning(f"⚠️ PostgreSQL connection failed: {e} - returning mock data")
            return generate_mock_data(query)


class MySQLExecutor(BaseExecutor):
    """MySQL database executor with demo mode support."""
    
    @staticmethod
    def _validate_config(connection_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate MySQL connection configuration.
        
        Returns:
            Tuple of (is_valid, missing_field)
        """
        required_fields = ["database", "user", "password"]
        for field in required_fields:
            if not connection_config.get(field):
                return False, field
        return True, None
    
    def execute(self, query: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query on MySQL database or return mock data in demo mode."""
        # Validate configuration
        is_valid, missing_field = self._validate_config(connection_config)
        
        if not is_valid:
            logging.info(f"🎭 MySQL demo mode: missing '{missing_field}' - returning mock data")
            return generate_mock_data(query)
        
        # Check if mysql-connector-python is installed
        try:
            import mysql.connector
        except ImportError:
            logging.info("🎭 MySQL demo mode: mysql-connector-python not installed - returning mock data")
            return generate_mock_data(query)
        
        try:
            conn = mysql.connector.connect(
                host=connection_config.get("host", "localhost"),
                port=connection_config.get("port", 3306),
                database=connection_config.get("database"),
                user=connection_config.get("user"),
                password=connection_config.get("password")
            )
            
            cursor = conn.cursor(dictionary=True)
            
            start = time.time()
            cursor.execute(query)
            rows = cursor.fetchall()
            execution_time = round(time.time() - start, 4)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = rows
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "columns": columns,
                "rows": result,
                "row_count": len(result),
                "execution_time": execution_time,
                "error": None
            }
            
        except Exception as e:
            logging.warning(f"⚠️ MySQL connection failed: {e} - returning mock data")
            return generate_mock_data(query)


class SQLServerExecutor(BaseExecutor):
    """SQL Server database executor with demo mode support."""
    
    @staticmethod
    def _validate_config(connection_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate SQL Server connection configuration.
        
        Returns:
            Tuple of (is_valid, missing_field)
        """
        required_fields = ["database", "user", "password"]
        for field in required_fields:
            if not connection_config.get(field):
                return False, field
        return True, None
    
    def execute(self, query: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query on SQL Server database or return mock data in demo mode."""
        # Validate configuration
        is_valid, missing_field = self._validate_config(connection_config)
        
        if not is_valid:
            logging.info(f"🎭 SQL Server demo mode: missing '{missing_field}' - returning mock data")
            return generate_mock_data(query)
        
        # Check if pyodbc is installed
        try:
            import pyodbc
        except ImportError:
            logging.info("🎭 SQL Server demo mode: pyodbc not installed - returning mock data")
            return generate_mock_data(query)
        
        try:
            # Build connection string
            driver = connection_config.get("driver", "{ODBC Driver 17 for SQL Server}")
            server = connection_config.get("host", "localhost")
            port = connection_config.get("port", 1433)
            database = connection_config.get("database")
            user = connection_config.get("user")
            password = connection_config.get("password")
            
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password}"
            )
            
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            start = time.time()
            cursor.execute(query)
            rows = cursor.fetchall()
            execution_time = round(time.time() - start, 4)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = [dict(zip(columns, row)) for row in rows]
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "columns": columns,
                "rows": result,
                "row_count": len(result),
                "execution_time": execution_time,
                "error": None
            }
            
        except Exception as e:
            logging.warning(f"⚠️ SQL Server connection failed: {e} - returning mock data")
            return generate_mock_data(query)
