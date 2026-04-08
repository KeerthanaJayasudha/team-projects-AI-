import re

def detect_intent(question, df):

    question = question.lower()

    columns = df.columns.tolist()

    intent = None
    x_col = None
    y_col = None
    agg = "sum"


    column_map = {
        "sales": "total_revenue",
        "revenue": "total_revenue",
        "income": "total_revenue",
        "region": "customer_region",
        "area": "customer_region",
        "date": "order_date",
        "time": "order_date",
        "profit": "profit",
        "orders": "order_id"
    }

    for key, value in column_map.items():
        question = question.replace(key, value)


    if "trend" in question or "over time" in question:
        intent = "trend"

    elif "compare" in question or "by" in question:
        intent = "comparison"

    elif "distribution" in question or "breakdown" in question:
        intent = "breakdown"

    else:
        intent = "comparison"


    for col in columns:

        if col.lower() in question:

            if "date" in col.lower():
                x_col = col

            elif "region" in col.lower():
                x_col = col

            elif "profit" in col.lower() or "revenue" in col.lower():
                y_col = col

    # Default fallback
    if x_col is None and "customer_region" in columns:
        x_col = "customer_region"

    if y_col is None and "total_revenue" in columns:
        y_col = "total_revenue"

    return intent, x_col, y_col, agg