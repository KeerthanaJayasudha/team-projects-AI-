# # import requests
# # import re
# # from llm_utils import extract_cypher

# # OLLAMA_URL = "http://localhost:11434/api/generate"


# # def generate_cypher(question, schema):

# #     # Detect visualization intent
# #     graph_keywords = [
# #         "graph",
# #         "visualize",
# #         "show relationships",
# #         "connected",
# #         "entity relationship",
# #         "hop"
# #     ]

# #     wants_graph = any(keyword in question.lower() for keyword in graph_keywords)

# #     hop_match = re.search(r'(\d+)[-\s]?hop', question.lower())
# #     k_hop = hop_match.group(1) if hop_match else None

# #     department_match = re.search(r'(sales|hr|research|development|marketing)', question.lower())
# #     department = department_match.group(1).capitalize() if department_match else None


# # #     prompt = f"""
# # # You are a Neo4j Cypher expert.

# # # STRICT RULES:

# # # Use this schema:

# # # {schema}

# # # Relationships allowed:

# # # (Employee)-[:WORKS_IN]->(Department)
# # # (Employee)-[:HAS_ROLE]->(JobRole)
# # # (Employee)-[:STUDIED]->(EducationField)
# # # (Employee)-[:TRAVELS]->(BusinessTravel)
# # # (Employee)-[:HAS_ATTRITION]->(Attrition)

# # # ALWAYS return graph paths using:

# # # MATCH p = (...)
# # # RETURN p
# # # LIMIT 10

# # # Never return tables like:
# # # RETURN e
# # # RETURN e,r,n

# # # Only return path variable p.

# # # Examples:

# # # Show employee relationships:

# # # MATCH p = (e:Employee)-[r]->(n)
# # # RETURN p
# # # LIMIT 10


# # # 2-hop graph of Sales employees:

# # # MATCH (e:Employee)-[:WORKS_IN]->(d:Department {{name:"Sales"}})
# # # MATCH p = (e)-[*1..2]-(n)
# # # RETURN p
# # # LIMIT 10


# # # User Question:
# # # {question}

# # # Generate Cypher query only.
# # # """

# # #     response = requests.post(
# # #         OLLAMA_URL,
# # #         json={
# # #             "model": "llama3",
# # #             "prompt": prompt,
# # #             "stream": False
# # #         }
# # #     )

# # #     raw_output = response.json()["response"]
# # #     cypher = extract_cypher(raw_output)

# # #     # Safety fallback
# # #     if "RETURN p" not in cypher:

# # #         cypher = """
# # # MATCH p = (e:Employee)-[r]->(n)
# # # RETURN p
# # # LIMIT 10
# # # """
# #     prompt = f"""
# # You are an expert Neo4j Cypher developer.

# # Convert the user question into a valid Cypher query.

# # Use this schema:

# # {schema}

# # Relationships:

# # (Employee)-[:WORKS_IN]->(Department)
# # (Employee)-[:HAS_ROLE]->(JobRole)
# # (Employee)-[:STUDIED]->(EducationField)
# # (Employee)-[:TRAVELS]->(BusinessTravel)
# # (Employee)-[:HAS_ATTRITION]->(Attrition)

# # STRICT RULES:
# # - Return ONLY the Cypher query
# # - Do NOT include explanations
# # - Do NOT include comments
# # - Do NOT include extra text
# # - employee_id is a NUMBER (not string)

# # IMPORTANT:

# # 1. For specific questions (like attrition, salary, etc):
# #    → Return direct query (NO path)

# # Example:
# # MATCH (e:Employee {{employee_id: 2}})-[:HAS_ATTRITION]->(a)
# # RETURN e,a

# # 2. For graph/relationship questions:
# #    → Use path

# # Example:
# # MATCH p = (e:Employee)-[r]->(n)
# # RETURN p
# # LIMIT 10

# # 3. For k-hop questions:
# # Example:
# # MATCH (e:Employee)-[:WORKS_IN]->(d:Department {{name:"Sales"}})
# # MATCH p = (e)-[*1..2]-(n)
# # RETURN p
# # LIMIT 10

# # User Question:
# # {question}

# # Cypher:
# # """
# #     response = requests.post(
# #         OLLAMA_URL,
# #         json={
# #             "model": "llama3",
# #             "prompt": prompt,
# #             "stream": False
# #         }
# #     )

# #     raw_output = response.json()["response"]

# #     # Extract only Cypher
# #     cypher = extract_cypher(raw_output)

# #     return cypher

import requests
import re
from llm_utils import extract_cypher

OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_cypher(question, schema):

    # Detect visualization intent
    graph_keywords = [
        "graph",
        "visualize",
        "show relationships",
        "connected",
        "entity relationship",
        "hop"
    ]

    wants_graph = any(keyword in question.lower() for keyword in graph_keywords)

    hop_match = re.search(r'(\d+)[-\s]?hop', question.lower())
    k_hop = hop_match.group(1) if hop_match else None

    department_match = re.search(r'(sales|hr|research|development|marketing)', question.lower())
    department = department_match.group(1).capitalize() if department_match else None


    prompt = f"""
You are a Neo4j Cypher expert.

STRICT RULES:

Use this schema:

{schema}

Relationships allowed:

(Employee)-[:WORKS_IN]->(Department)
(Employee)-[:HAS_ROLE]->(JobRole)
(Employee)-[:STUDIED]->(EducationField)
(Employee)-[:TRAVELS]->(BusinessTravel)
(Employee)-[:HAS_ATTRITION]->(Attrition)

ALWAYS return graph paths using:

MATCH p = (...)
RETURN p
LIMIT 10

Never return tables like:
RETURN e
RETURN e,r,n

Only return path variable p.

Examples:

Show employee relationships:

MATCH p = (e:Employee)-[r]->(n)
RETURN p
LIMIT 10


2-hop graph of Sales employees:

MATCH (e:Employee)-[:WORKS_IN]->(d:Department {{name:"Sales"}})
MATCH p = (e)-[*1..2]-(n)
RETURN p
LIMIT 10


User Question:
{question}

Generate Cypher query only.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    raw_output = response.json()["response"]
    cypher = extract_cypher(raw_output)

    # Safety fallback
    if "RETURN p" not in cypher:

        cypher = """
MATCH p = (e:Employee)-[r]->(n)
RETURN p
LIMIT 10
"""

    return cypher
 
# import requests
# import re
# from llm_utils import extract_cypher

# OLLAMA_URL = "http://localhost:11434/api/generate"


# def generate_cypher(question, schema):

#     # Detect visualization intent
#     graph_keywords = [
#         "graph",
#         "visualize",
#         "show relationships",
#         "connected",
#         "entity relationship",
#         "hop"
#     ]

#     wants_graph = any(keyword in question.lower() for keyword in graph_keywords)

#     hop_match = re.search(r'(\d+)[-\s]?hop', question.lower())
#     k_hop = hop_match.group(1) if hop_match else None

#     department_match = re.search(r'(sales|hr|research|development|marketing)', question.lower())
#     department = department_match.group(1).capitalize() if department_match else None


#     prompt = f"""
# You are a Neo4j Cypher expert.

# STRICT RULES:

# Use this schema:

# {schema}

# Relationships allowed:

# (Employee)-[:WORKS_IN]->(Department)
# (Employee)-[:HAS_ROLE]->(JobRole)
# (Employee)-[:STUDIED]->(EducationField)
# (Employee)-[:TRAVELS]->(BusinessTravel)
# (Employee)-[:HAS_ATTRITION]->(Attrition)

# ALWAYS return graph paths using:

# MATCH p = (...)
# RETURN p
# LIMIT 10

# Never return tables like:
# RETURN e
# RETURN e,r,n

# Only return path variable p.

# Examples:

# Show employee relationships:

# MATCH p = (e:Employee)-[r]->(n)
# RETURN p
# LIMIT 10


# 2-hop graph of Sales employees:

# MATCH (e:Employee)-[:WORKS_IN]->(d:Department {{name:"Sales"}})
# MATCH p = (e)-[*1..2]-(n)
# RETURN p
# LIMIT 10


# User Question:
# {question}

# Generate Cypher query only.
# """

#     response = requests.post(
#         OLLAMA_URL,
#         json={
#             "model": "llama3",
#             "prompt": prompt,
#             "stream": False
#         }
#     )

#     raw_output = response.json()["response"]
#     cypher = extract_cypher(raw_output)

#     # Safety fallback
#     if "RETURN p" not in cypher:

#         cypher = """
# MATCH p = (e:Employee)-[r]->(n)
# RETURN p
# LIMIT 10
# """

#     return cypher
