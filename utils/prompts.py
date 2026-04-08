INTENT_PROMPT = """
You are a BI assistant.

Numeric columns:
{numeric_columns}

Categorical columns:
{categorical_columns}

User Question:
{question}

Return ONLY this format:

intent: <trend/comparison/distribution/kpi>
x_column: <column name>
y_column: <column name>
aggregation: <sum/mean/count>
"""

INSIGHT_PROMPT = """
User asked:
{question}

Aggregated data:
{data}

Write a short professional business insight.
"""