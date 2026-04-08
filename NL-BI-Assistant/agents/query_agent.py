def run_query(df, x_col, y_col, aggregation):

    if x_col not in df.columns or y_col not in df.columns:
        return None

    if aggregation == "sum":
        result = df.groupby(x_col)[y_col].sum().reset_index()

    elif aggregation == "mean":
        result = df.groupby(x_col)[y_col].mean().reset_index()

    elif aggregation == "count":
        result = df.groupby(x_col)[y_col].count().reset_index()

    else:
        result = df.groupby(x_col)[y_col].sum().reset_index()

    return result