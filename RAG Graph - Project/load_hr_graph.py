import pandas as pd
from neo4j import GraphDatabase

# Neo4j credentials
URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "neo4j123"  # replace if different

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Load CSV
df = pd.read_csv("WA_Fn-UseC_-HR-Employee-Attrition.csv")

def create_employee_graph(tx, row):
    tx.run("""
        MERGE (e:Employee {employee_id: $employee_id})
        SET e.age = $age,
            e.gender = $gender,
            e.monthly_income = $monthly_income,
            e.job_level = $job_level

        MERGE (d:Department {name: $department})
        MERGE (r:JobRole {name: $job_role})
        MERGE (edu:EducationField {name: $education_field})
        MERGE (t:BusinessTravel {type: $business_travel})
        MERGE (a:Attrition {status: $attrition})

        MERGE (e)-[:WORKS_IN]->(d)
        MERGE (e)-[:HAS_ROLE]->(r)
        MERGE (e)-[:STUDIED]->(edu)
        MERGE (e)-[:TRAVELS]->(t)
        MERGE (e)-[:HAS_ATTRITION]->(a)
    """, {
        # ✅ FIXED HERE
        "employee_id": row["EmployeeNumber"],

        "age": row["Age"],
        "gender": row["Gender"],
        "monthly_income": row["MonthlyIncome"],
        "job_level": row["JobLevel"],
        "department": row["Department"],
        "job_role": row["JobRole"],
        "education_field": row["EducationField"],
        "business_travel": row["BusinessTravel"],
        "attrition": row["Attrition"]
    })

with driver.session() as session:
    for _, row in df.iterrows():
        session.execute_write(create_employee_graph, row)

driver.close()

print("HR Graph Loaded Successfully!")
