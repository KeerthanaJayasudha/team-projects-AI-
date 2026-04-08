import pandas as pd
import duckdb
import tempfile


def load_data(uploaded_file, engine):

    file_type = uploaded_file.name.split(".")[-1]

    if file_type == "xlsx":
        file_type = "excel"

    # -------------------------
    # Pandas Engine
    # -------------------------
    if engine == "Pandas":

        if file_type == "csv":
            df = pd.read_csv(uploaded_file)

        elif file_type == "excel":
            df = pd.read_excel(uploaded_file)

        elif file_type == "json":
            df = pd.read_json(uploaded_file)

        return df, None

    # -------------------------
    # DuckDB Engine
    # -------------------------
    else:

        con = duckdb.connect()

        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(uploaded_file.read())
        temp.close()

        path = temp.name

        if file_type == "csv":
            query = f"SELECT * FROM read_csv_auto('{path}')"

        elif file_type == "json":
            query = f"SELECT * FROM read_json_auto('{path}')"

        elif file_type == "excel":
            df = pd.read_excel(path)
            con.register("dataset", df)
            return df, con

        df = con.execute(query).fetchdf()
        con.register("dataset", df)

        return df, con