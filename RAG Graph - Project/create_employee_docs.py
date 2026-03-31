import pandas as pd
import json

df = pd.read_csv("WA_Fn-UseC_-HR-Employee-Attrition.csv")

docs = []

for i, row in df.iterrows():

    text = f"""
    Employee {i} works in {row['Department']} department.
    Job role: {row['JobRole']}.
    Education field: {row['EducationField']}.
    Monthly income: {row['MonthlyIncome']}.
    Business travel: {row['BusinessTravel']}.
    Attrition status: {row['Attrition']}.
    """

    docs.append({
        "employee_id": str(i),
        "text": text
    })

with open("employee_docs.json", "w") as f:
    json.dump(docs, f, indent=2)
