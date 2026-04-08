import pandas as pd
from sqlalchemy import create_engine, inspect

def connect_database(db_type, host, port, user, password, database):

    if db_type == "MySQL":
        conn = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    elif db_type == "PostgreSQL":
        conn = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    elif db_type == "SQL Server":
        conn = f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

    engine = create_engine(conn)

    return engine


def get_tables(engine):

    inspector = inspect(engine)

    return inspector.get_table_names()


def load_table(engine, table):

    df = pd.read_sql(f"SELECT * FROM {table}", engine)

    return df