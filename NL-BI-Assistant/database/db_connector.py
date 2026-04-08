from sqlalchemy import create_engine
import pandas as pd


def create_db_engine(db_type, host, port, username, password, database):

    if db_type == "postgresql":
        connection_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

    elif db_type == "mysql":
        connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

    else:
        raise ValueError("Unsupported database")

    engine = create_engine(connection_string)

    return engine


def load_table(engine, table_name):

    query = f"SELECT * FROM {table_name}"

    df = pd.read_sql(query, engine)

    return df


def save_table(engine, df, table_name):

    df.to_sql(table_name, engine, if_exists="replace", index=False)