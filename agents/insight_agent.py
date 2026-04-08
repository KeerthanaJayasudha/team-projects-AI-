import pandas as pd

def generate_insight(question, result):

    try:

        # If result is empty
        if result is None or result.empty:
            return "No data available to generate insight."

        columns = result.columns.tolist()

        x_col = columns[0]
        y_col = columns[1]

        # Find max and min values
        max_row = result.loc[result[y_col].idxmax()]
        min_row = result.loc[result[y_col].idxmin()]

        max_category = max_row[x_col]
        max_value = max_row[y_col]

        min_category = min_row[x_col]
        min_value = min_row[y_col]

        total = result[y_col].sum()
        avg = result[y_col].mean()

        insight = f"""
Key Insight 📊

• The highest {y_col} is in **{max_category}** with value **{round(max_value,2)}**.

• The lowest {y_col} is in **{min_category}** with value **{round(min_value,2)}**.

• The total {y_col} across all categories is **{round(total,2)}**.

• The average {y_col} is **{round(avg,2)}**.

This indicates that **{max_category}** is the top performing segment.
"""

        return insight

    except Exception as e:

        return f"Insight generation failed: {e}"