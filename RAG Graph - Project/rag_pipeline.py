
# from neo4j import GraphDatabase
# from query_generator import generate_cypher
# from vector_store import VectorStore
# from context_builder import format_context
# from answer_generator import generate_answer
# import re
# from llm_utils import call_llm, extract_cypher


# # Load vector store
# vector_store = VectorStore("employee_docs.json")


# # Neo4j connection
# URI = "bolt://localhost:7687"
# USERNAME = "neo4j"
# PASSWORD = "neo4j123"

# driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


# # Schema definition for validation
# SCHEMA = {
#     "nodes": {
#         "Employee": ["employee_id", "age", "gender", "monthly_income", "job_level"],
#         "Department": ["name"],
#         "JobRole": ["name"],
#         "EducationField": ["name"],
#         "BusinessTravel": ["type"],
#         "Attrition": ["status"]
#     },
#     "relationships": {
#         "WORKS_IN": ("Employee", "Department"),
#         "HAS_ROLE": ("Employee", "JobRole"),
#         "STUDIED": ("Employee", "EducationField"),
#         "TRAVELS": ("Employee", "BusinessTravel"),
#         "HAS_ATTRITION": ("Employee", "Attrition")
#     }
# }


# def validate_and_correct_cypher(cypher):
#     """
#     Validates and corrects common Cypher query mistakes based on schema.
    
#     Common fixes:
#     1. Employee {name:"Sales"} → Department {name:"Sales"}
#     2. Department -[:HAS_ROLE]-> JobRole → Employee -[:HAS_ROLE]-> JobRole
#     3. Invalid properties on nodes
#     4. Invalid relationship directions
#     """
    
#     corrected = cypher
#     corrections_made = []
    
#     # Fix 1: Employee with "name" property containing department names
#     # This is the most common mistake - Employee {name:"Sales"} should be Department {name:"Sales"}
#     department_names = ["Sales", "HR", "Research", "Development", "Marketing", 
#                        "Research & Development", "Human Resources"]
    
#     for dept_name in department_names:
#         # Match Employee node with name property and department value
#         # Pattern: (:Employee {name:"Sales"}) or (e:Employee {name:"Sales"})
#         pattern = r'\(\s*(\w*)\s*:Employee\s*\{\s*name\s*:\s*["\']' + re.escape(dept_name) + r'["\']\s*\}\s*\)'
#         if re.search(pattern, corrected, re.IGNORECASE):
#             # Replace with Department node, preserving variable name if present
#             def replace_func(match):
#                 var_name = match.group(1) if match.group(1) else 'd'
#                 return f'({var_name}:Department {{name:"{dept_name}"}})'
            
#             corrected = re.sub(pattern, replace_func, corrected, flags=re.IGNORECASE)
#             corrections_made.append(f"Fixed: Employee {{name:\"{dept_name}\"}} → Department {{name:\"{dept_name}\"}}")
    
#     # Fix 2: Incorrect relationship endpoints - Department with relationships that should be Employee
    
#     # Department -[:HAS_ROLE]-> JobRole
#     pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:HAS_ROLE[^\]]*)\]->\s*\((\s*\w*\s*:JobRole[^)]*)\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             var_name = match.group(1) if match.group(1) else 'e'
#             rel = match.group(3)
#             job_role = match.group(4)
#             return f'({var_name}:Employee)-[{rel}]->({job_role})'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Fixed: Department -[:HAS_ROLE]-> JobRole → Employee -[:HAS_ROLE]-> JobRole")
    
#     # Department -[:STUDIED]-> EducationField
#     pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:STUDIED[^\]]*)\]->\s*\((\s*\w*\s*:EducationField[^)]*)\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             var_name = match.group(1) if match.group(1) else 'e'
#             rel = match.group(3)
#             edu_field = match.group(4)
#             return f'({var_name}:Employee)-[{rel}]->({edu_field})'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Fixed: Department -[:STUDIED]-> EducationField → Employee -[:STUDIED]-> EducationField")
    
#     # Department -[:TRAVELS]-> BusinessTravel
#     pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:TRAVELS[^\]]*)\]->\s*\((\s*\w*\s*:BusinessTravel[^)]*)\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             var_name = match.group(1) if match.group(1) else 'e'
#             rel = match.group(3)
#             travel = match.group(4)
#             return f'({var_name}:Employee)-[{rel}]->({travel})'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Fixed: Department -[:TRAVELS]-> BusinessTravel → Employee -[:TRAVELS]-> BusinessTravel")
    
#     # Department -[:HAS_ATTRITION]-> Attrition
#     pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:HAS_ATTRITION[^\]]*)\]->\s*\((\s*\w*\s*:Attrition[^)]*)\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             var_name = match.group(1) if match.group(1) else 'e'
#             rel = match.group(3)
#             attrition = match.group(4)
#             return f'({var_name}:Employee)-[{rel}]->({attrition})'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Fixed: Department -[:HAS_ATTRITION]-> Attrition → Employee -[:HAS_ATTRITION]-> Attrition")
    
#     # Fix 3: Reverse relationship directions
#     # WORKS_IN should be Employee -> Department (not Department -> Employee)
#     pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:WORKS_IN[^\]]*)\]->\s*\(\s*(\w*)\s*:Employee([^)]*)\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             dept_var = match.group(1) if match.group(1) else 'd'
#             dept_props = match.group(2)
#             rel = match.group(3)
#             emp_var = match.group(4) if match.group(4) else 'e'
#             emp_props = match.group(5)
#             return f'({emp_var}:Employee{emp_props})-[{rel}]->({dept_var}:Department{dept_props})'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Fixed: Department -[:WORKS_IN]-> Employee → Employee -[:WORKS_IN]-> Department")
    
#     # Fix 4: Bidirectional relationships that should be directional
#     # Replace -[:WORKS_IN]- with -[:WORKS_IN]-> when appropriate
#     pattern = r'\(\s*(\w*)\s*:Employee([^)]*)\)\s*-\[:WORKS_IN\]-\s*\(\s*(\w*)\s*:Department([^)]*)\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             emp_var = match.group(1) if match.group(1) else 'e'
#             emp_props = match.group(2)
#             dept_var = match.group(3) if match.group(3) else 'd'
#             dept_props = match.group(4)
#             return f'({emp_var}:Employee{emp_props})-[:WORKS_IN]->({dept_var}:Department{dept_props})'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Fixed: Employee -[:WORKS_IN]- Department → Employee -[:WORKS_IN]-> Department")
    
#     # Fix 5: Remove remaining invalid "name" properties from Employee nodes
#     # This catches any Employee {name:...} that wasn't a department name
#     pattern = r'\(\s*(\w*)\s*:Employee\s*\{\s*name\s*:\s*["\'][^"\']*["\']\s*\}\s*\)'
#     if re.search(pattern, corrected):
#         def replace_func(match):
#             var_name = match.group(1) if match.group(1) else 'e'
#             return f'({var_name}:Employee)'
        
#         corrected = re.sub(pattern, replace_func, corrected)
#         corrections_made.append("Removed invalid 'name' property from Employee node")
    
#     # Fix 6: JobRole with "title" instead of "name"
#     pattern = r':JobRole\s*\{\s*title\s*:'
#     if re.search(pattern, corrected):
#         corrected = re.sub(pattern, ':JobRole {name:', corrected)
#         corrections_made.append("Fixed: JobRole {title:...} → JobRole {name:...}")
    
#     # Fix 7: Department with "dept_name" instead of "name"
#     pattern = r':Department\s*\{\s*dept_name\s*:'
#     if re.search(pattern, corrected):
#         corrected = re.sub(pattern, ':Department {name:', corrected)
#         corrections_made.append("Fixed: Department {dept_name:...} → Department {name:...}")
    
#     # Print corrections if any were made
#     if corrections_made:
#         print("\n⚠️  Cypher Query Corrections Applied:")
#         for correction in corrections_made:
#             print(f"   - {correction}")
#         print()
    
#     return corrected


# def run_cypher_query(query):

#     nodes = {}
#     relationships = []
#     relationship_ids = set()
#     records = []

#     with driver.session() as session:

#         result = session.run(query)

#         for record in result:

#             records.append(record.data())

#             for value in record.values():

#                 # Handle Path results
#                 if hasattr(value, "nodes") and hasattr(value, "relationships"):

#                     # Extract nodes from path
#                     path_nodes = list(value.nodes)
#                     path_rels = list(value.relationships)

#                     # Add all nodes from the path
#                     for node in path_nodes:

#                         node_id = node.id

#                         if node_id not in nodes:
#                             # Convert node properties to dict, handling Neo4j types
#                             node_props = {}
#                             for key in node.keys():
#                                 node_props[key] = node[key]
                            
#                             nodes[node_id] = {
#                                 "id": node_id,
#                                 "label": list(node.labels)[0] if node.labels else "Node",
#                                 "properties": node_props
#                             }

#                     # Add relationships using their actual start/end nodes
#                     for rel in path_rels:

#                         # Get the actual start and end node IDs from the relationship
#                         # These preserve the true direction regardless of path traversal
#                         start_node_id = rel.start_node.id
#                         end_node_id = rel.end_node.id

#                         rel_id = (
#                             start_node_id,
#                             end_node_id,
#                             rel.type
#                         )

#                         if rel_id not in relationship_ids:

#                             relationship_ids.add(rel_id)

#                             relationships.append({
#                                 "start": start_node_id,
#                                 "end": end_node_id,
#                                 "type": rel.type
#                             })

#                 # Handle individual Node results
#                 elif hasattr(value, "id") and hasattr(value, "labels"):

#                     node_id = value.id

#                     if node_id not in nodes:
#                         # Convert node properties to dict
#                         node_props = {}
#                         for key in value.keys():
#                             node_props[key] = value[key]
                        
#                         nodes[node_id] = {
#                             "id": node_id,
#                             "label": list(value.labels)[0] if value.labels else "Node",
#                             "properties": node_props
#                         }

#     return {
#         "records": records,
#         "nodes": list(nodes.values()),
#         "relationships": relationships
#     }


# # def ask_question(question):

# #     schema = """
# # Graph Schema:

# # Nodes:

# # Employee
# # - employee_id
# # - age
# # - gender
# # - monthly_income
# # - job_level

# # Department
# # - name

# # JobRole
# # - name

# # EducationField
# # - name

# # BusinessTravel
# # - type

# # Attrition
# # - status

# # Relationships:

# # (:Employee)-[:WORKS_IN]->(:Department)
# # (:Employee)-[:HAS_ROLE]->(:JobRole)
# # (:Employee)-[:STUDIED]->(:EducationField)
# # (:Employee)-[:TRAVELS]->(:BusinessTravel)
# # (:Employee)-[:HAS_ATTRITION]->(:Attrition)
# # """
# #     cypher = generate_cypher(question)

# # # Fix invalid RETURN pattern generated by LLM
# #     if "RETURN p =" in cypher:
# #         cypher = cypher.replace("RETURN p =", "MATCH p =")

# #     graph_data = run_cypher_query(cypher)

# #     # Step 1 — Generate Cypher
# #     cypher = generate_cypher(question, schema)

# #     # Step 2 — Validate and Correct Cypher
# #     cypher = validate_and_correct_cypher(cypher)

# #     # Safety fix for bad LLM output
# #     if "relationship type" in cypher.lower():

# #         cypher = """
# # MATCH p = (e:Employee)-[r]->(n)
# # RETURN p
# # LIMIT 10
# # """

# #     # Ensure LIMIT exists
# #     if "LIMIT" not in cypher.upper():
# #         cypher += "\nLIMIT 10"

# #     # Step 3 — Query Neo4j
# #     graph_data = run_cypher_query(cypher)

# #     graph_results = graph_data["records"]
# #     nodes = graph_data["nodes"]
# #     # Extract employee ids from graph results
# #     graph_employee_ids = set()

# #     for node in nodes:
# #         if node["label"] == "Employee":
# #            emp_id = node["properties"].get("employee_id")
# #            if emp_id is not None:
# #             graph_employee_ids.add(emp_id)
# #     print("Graph Employees:", graph_employee_ids)   
    
# #     relationships = graph_data["relationships"]
    
# def ask_question(question):

#     schema = """
# Graph Schema:

# Nodes:

# Employee
# - employee_id
# - age
# - gender
# - monthly_income
# - job_level

# Department
# - name

# JobRole
# - name

# EducationField
# - name

# BusinessTravel
# - type

# Attrition
# - status

# Relationships:

# (:Employee)-[:WORKS_IN]->(:Department)
# (:Employee)-[:HAS_ROLE]->(:JobRole)
# (:Employee)-[:STUDIED]->(:EducationField)
# (:Employee)-[:TRAVELS]->(:BusinessTravel)
# (:Employee)-[:HAS_ATTRITION]->(:Attrition)
# Important Query Rules:

# 1. Employees connect to departments using:
# (:Employee)-[:WORKS_IN]->(:Department)

# 2. Department nodes have property:
# name

# Examples of department names:
# Sales
# Research & Development
# Human Resources

# 3. When filtering by department name ALWAYS use:
# (:Department {name:"Sales"})

# 4. NEVER use department names as Employee properties.

# Example:
# WRONG:
# (:Employee {name:"Sales"})

# CORRECT:
# (:Employee)-[:WORKS_IN]->(:Department {name:"Sales"})
# """

# #     # Step 1 — Generate Cypher
    
# #     cypher_raw = generate_cypher(question, schema)
# #     cypher = extract_cypher(cypher_raw)
# #     # Step 2 — Validate and Correct Cypher
# #     cypher = validate_and_correct_cypher(cypher)
# #     print("Raw LLM Output:", cypher_raw)
# #     print("Clean Cypher:", cypher)

# #     if "RETURN p =" in cypher:
# #         cypher = cypher.replace("RETURN p =", "MATCH p =")
# #     # Ensure p exists for visualization
# #     if "RETURN p" in cypher and "MATCH p =" not in cypher:
# #         cypher = cypher.replace("RETURN p", "MATCH p = (e)-[*1..1]")
# #     # Fix invalid RETURN pattern generated by LLM
# #     if "RETURN p =" in cypher:
# #         cypher = cypher.replace("RETURN p =", "MATCH p =")

# #     # Safety fix for bad LLM output
# #     if "relationship type" in cypher.lower():

# #         cypher = """
# # MATCH (e:Employee)-[r]->(n)
# # RETURN e,r,n
# # LIMIT 10
# # """

# #     # Ensure LIMIT exists
# #     if "RETURN" not in cypher.upper():
# #         cypher = """
# # MATCH (e:Employee)-[r]->(n)
# # RETURN e,r,n
# # LIMIT 10
# # """
# #     elif "LIMIT" not in cypher.upper():
# #         cypher += "\nLIMIT 10"

# #     print("Generated Cypher Query:")
# #     print(cypher)
#     # Step 1 — Generate Cypher
#     cypher_raw = generate_cypher(question, schema)
#     cypher = extract_cypher(cypher_raw)

# # Step 2 — Validate and Correct Cypher
#     cypher = validate_and_correct_cypher(cypher)
#     # Ensure Employee is always returned
#     if "RETURN" in cypher and "e" not in cypher.split("RETURN")[1]:
#         print("⚠️ Fixing missing Employee in RETURN")
#         cypher = cypher.replace("RETURN", "RETURN e, ")

#     print("Raw LLM Output:", cypher_raw)
#     print("Clean Cypher:", cypher)

# # Fix invalid RETURN pattern generated by LLM
#     if "RETURN p =" in cypher:
#         cypher = cypher.replace("RETURN p =", "MATCH p =")
        

# # Ensure path variable exists
#     # if "RETURN p" in cypher and "MATCH p =" not in cypher:
#     #     cypher = cypher.replace("RETURN p", "MATCH p = (e)-[*1..1]-(n) RETURN p")

# # Safety fix for bad LLM output
#     if "relationship type" in cypher.lower():
#        cypher = """
# MATCH p = (e:Employee)-[r]->(n)
# RETURN e,r,n
# LIMIT 10
# """

# # Ensure RETURN exists
#     if "RETURN" not in cypher.upper():
#         cypher = """
# MATCH p = (e:Employee)-[r]->(n)
# RETURN p
# LIMIT 10
# """

# # Ensure LIMIT exists
#     if "LIMIT" not in cypher.upper():
#         cypher += "\nLIMIT 10"

#     print("Generated Cypher Query:")
#     print(cypher)
#     # Step 3 — Query Neo4j
#     if not cypher.strip().upper().startswith("MATCH"):
#         cypher = """
# MATCH (e:Employee)-[r]->(n)
# RETURN e,r,n
# LIMIT 5
# """
#     # Fix missing path variable
#     if "RETURN p" in cypher and "MATCH p =" not in cypher:
#         cypher = cypher.replace("MATCH", "MATCH p =")
#     graph_data = run_cypher_query(cypher)

#     # graph_results = graph_data["records"]
#     # nodes = graph_data["nodes"]

#     # # Extract employee ids from graph results
#     # graph_employee_ids = set()

#     # for node in nodes:
#     #     if node["label"] == "Employee":
#     #         emp_id = node["properties"].get("employee_id")
#     #         if emp_id is not None:
#     #             graph_employee_ids.add(emp_id)
#     graph_results = graph_data["records"]
#     nodes = graph_data["nodes"]

# # Extract employee ids from graph RESULTS (not nodes)
#     graph_employee_ids = set()

#     # for record in graph_results:
#     #     for value in record.values():

#     #     # Case 1: value is a dict (common case)
#     #         if isinstance(value, dict):
#     #             if value.get("label") == "Employee":
#     #                 emp_id = value.get("properties", {}).get("employee_id")

#     #                 if emp_id is not None:
#     #                     graph_employee_ids.add(emp_id)

#     #     # Case 2: fallback (rare cases)
#     #         elif hasattr(value, "get"):
#     #             emp_id = value.get("employee_id")

#     #             if emp_id is not None:
#     #                 graph_employee_ids.add(emp_id)

#     # print("Graph Employees:", graph_employee_ids)
#     graph_employee_ids = set()

#     for record in graph_results:
#         for value in record.values():

#         # ✅ HANDLE Neo4j Node objects (THIS IS THE FIX)
#             if hasattr(value, "labels") and hasattr(value, "items"):

#                 if "Employee" in list(value.labels):
#                     emp_id = value.get("employee_id")

#                     if emp_id is not None:
#                         graph_employee_ids.add(emp_id)

#         # (optional fallback)
#             elif isinstance(value, dict):
#                 if value.get("label") == "Employee":
#                     emp_id = value.get("properties", {}).get("employee_id")

#                     if emp_id is not None:
#                         graph_employee_ids.add(emp_id)

#     print("Graph Employees:", graph_employee_ids)
    

#     relationships = graph_data["relationships"]
#     # Step 4 — Vector Search
#     vector_candidates = vector_store.search(question, k=50)

#     vector_results = []
#     # Filter vector results to only include documents about employees in graph results
#     for doc in vector_candidates:

#     # Get employee_id directly from JSON
#         doc_employee_id = doc.get("employee_id")

#         if doc_employee_id is None:
#             continue
        
#         doc_employee_id = int(doc_employee_id)
#     # Check if employee exists in graph results
#         if doc_employee_id in graph_employee_ids:
#             vector_results.append(doc)
    
#     print("Vector Documents:")
#     for doc in vector_results:
#         print(doc["text"])        
#     print("Vector Results Found:", len(vector_results))      
    
#     vector_text = ""
#     for doc in vector_results:
#         vector_text += doc["text"] + "\n"
#     # Step 4 — Retrieve vector documents for graph employees

#     # vector_results = []

#     # for doc in vector_store.docs:

#     #     text = doc["text"]

#     #     for emp_id in graph_employee_ids:

#     #         emp_string = f"Employee {emp_id}"

#     #         if emp_string in text:
#     #             vector_results.append(doc)
#     #             break


#     # print("Vector Documents:")
#     # for doc in vector_results:
#     #     print(doc["text"])

#     # print("Vector Results Found:", len(vector_results))


#     # vector_text = ""
#     # for doc in vector_results:
#     #     vector_text += doc["text"] + "\n"
#     # Step 5 — Build Graph Context
#     graph_context = format_context(graph_results)

#     reasoning_context = f"""
# User Question:
# {question}

# Cypher Query:
# {cypher}

# Graph Data:
# {graph_context}

# Vector Documents:
# {vector_text}
# """

#     # Step 6 — Generate Answer
#     answer = generate_answer(question, reasoning_context)

#     return {
#         "cypher": cypher,
#         "graph_results": graph_results,
#         "nodes": nodes,
#         "relationships": relationships,
#         "vector_results": vector_results,
#         "answer": answer,
#         "graph_employees": list(graph_employee_ids)
#     }

 

from neo4j import GraphDatabase
from query_generator import generate_cypher
from vector_store import VectorStore
from context_builder import format_context
from answer_generator import generate_answer
import re
from llm_utils import call_llm, extract_cypher


# Load vector store
vector_store = VectorStore("employee_docs.json")


# Neo4j connection
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "neo4j123"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


# Schema definition for validation
SCHEMA = {
    "nodes": {
        "Employee": ["employee_id", "age", "gender", "monthly_income", "job_level"],
        "Department": ["name"],
        "JobRole": ["name"],
        "EducationField": ["name"],
        "BusinessTravel": ["type"],
        "Attrition": ["status"]
    },
    "relationships": {
        "WORKS_IN": ("Employee", "Department"),
        "HAS_ROLE": ("Employee", "JobRole"),
        "STUDIED": ("Employee", "EducationField"),
        "TRAVELS": ("Employee", "BusinessTravel"),
        "HAS_ATTRITION": ("Employee", "Attrition")
    }
}


def validate_and_correct_cypher(cypher):
    """
    Validates and corrects common Cypher query mistakes based on schema.
    
    Common fixes:
    1. Employee {name:"Sales"} → Department {name:"Sales"}
    2. Department -[:HAS_ROLE]-> JobRole → Employee -[:HAS_ROLE]-> JobRole
    3. Invalid properties on nodes
    4. Invalid relationship directions
    """
    
    corrected = cypher
    corrections_made = []
    
    # Fix 1: Employee with "name" property containing department names
    # This is the most common mistake - Employee {name:"Sales"} should be Department {name:"Sales"}
    department_names = ["Sales", "HR", "Research", "Development", "Marketing", 
                       "Research & Development", "Human Resources"]
    
    for dept_name in department_names:
        # Match Employee node with name property and department value
        # Pattern: (:Employee {name:"Sales"}) or (e:Employee {name:"Sales"})
        pattern = r'\(\s*(\w*)\s*:Employee\s*\{\s*name\s*:\s*["\']' + re.escape(dept_name) + r'["\']\s*\}\s*\)'
        if re.search(pattern, corrected, re.IGNORECASE):
            # Replace with Department node, preserving variable name if present
            def replace_func(match):
                var_name = match.group(1) if match.group(1) else 'd'
                return f'({var_name}:Department {{name:"{dept_name}"}})'
            
            corrected = re.sub(pattern, replace_func, corrected, flags=re.IGNORECASE)
            corrections_made.append(f"Fixed: Employee {{name:\"{dept_name}\"}} → Department {{name:\"{dept_name}\"}}")
    
    # Fix 2: Incorrect relationship endpoints - Department with relationships that should be Employee
    
    # Department -[:HAS_ROLE]-> JobRole
    pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:HAS_ROLE[^\]]*)\]->\s*\((\s*\w*\s*:JobRole[^)]*)\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            var_name = match.group(1) if match.group(1) else 'e'
            rel = match.group(3)
            job_role = match.group(4)
            return f'({var_name}:Employee)-[{rel}]->({job_role})'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Fixed: Department -[:HAS_ROLE]-> JobRole → Employee -[:HAS_ROLE]-> JobRole")
    
    # Department -[:STUDIED]-> EducationField
    pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:STUDIED[^\]]*)\]->\s*\((\s*\w*\s*:EducationField[^)]*)\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            var_name = match.group(1) if match.group(1) else 'e'
            rel = match.group(3)
            edu_field = match.group(4)
            return f'({var_name}:Employee)-[{rel}]->({edu_field})'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Fixed: Department -[:STUDIED]-> EducationField → Employee -[:STUDIED]-> EducationField")
    
    # Department -[:TRAVELS]-> BusinessTravel
    pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:TRAVELS[^\]]*)\]->\s*\((\s*\w*\s*:BusinessTravel[^)]*)\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            var_name = match.group(1) if match.group(1) else 'e'
            rel = match.group(3)
            travel = match.group(4)
            return f'({var_name}:Employee)-[{rel}]->({travel})'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Fixed: Department -[:TRAVELS]-> BusinessTravel → Employee -[:TRAVELS]-> BusinessTravel")
    
    # Department -[:HAS_ATTRITION]-> Attrition
    pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:HAS_ATTRITION[^\]]*)\]->\s*\((\s*\w*\s*:Attrition[^)]*)\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            var_name = match.group(1) if match.group(1) else 'e'
            rel = match.group(3)
            attrition = match.group(4)
            return f'({var_name}:Employee)-[{rel}]->({attrition})'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Fixed: Department -[:HAS_ATTRITION]-> Attrition → Employee -[:HAS_ATTRITION]-> Attrition")
    
    # Fix 3: Reverse relationship directions
    # WORKS_IN should be Employee -> Department (not Department -> Employee)
    pattern = r'\(\s*(\w*)\s*:Department([^)]*)\)\s*-\[([^\]]*:WORKS_IN[^\]]*)\]->\s*\(\s*(\w*)\s*:Employee([^)]*)\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            dept_var = match.group(1) if match.group(1) else 'd'
            dept_props = match.group(2)
            rel = match.group(3)
            emp_var = match.group(4) if match.group(4) else 'e'
            emp_props = match.group(5)
            return f'({emp_var}:Employee{emp_props})-[{rel}]->({dept_var}:Department{dept_props})'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Fixed: Department -[:WORKS_IN]-> Employee → Employee -[:WORKS_IN]-> Department")
    
    # Fix 4: Bidirectional relationships that should be directional
    # Replace -[:WORKS_IN]- with -[:WORKS_IN]-> when appropriate
    pattern = r'\(\s*(\w*)\s*:Employee([^)]*)\)\s*-\[:WORKS_IN\]-\s*\(\s*(\w*)\s*:Department([^)]*)\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            emp_var = match.group(1) if match.group(1) else 'e'
            emp_props = match.group(2)
            dept_var = match.group(3) if match.group(3) else 'd'
            dept_props = match.group(4)
            return f'({emp_var}:Employee{emp_props})-[:WORKS_IN]->({dept_var}:Department{dept_props})'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Fixed: Employee -[:WORKS_IN]- Department → Employee -[:WORKS_IN]-> Department")
    
    # Fix 5: Remove remaining invalid "name" properties from Employee nodes
    # This catches any Employee {name:...} that wasn't a department name
    pattern = r'\(\s*(\w*)\s*:Employee\s*\{\s*name\s*:\s*["\'][^"\']*["\']\s*\}\s*\)'
    if re.search(pattern, corrected):
        def replace_func(match):
            var_name = match.group(1) if match.group(1) else 'e'
            return f'({var_name}:Employee)'
        
        corrected = re.sub(pattern, replace_func, corrected)
        corrections_made.append("Removed invalid 'name' property from Employee node")
    
    # Fix 6: JobRole with "title" instead of "name"
    pattern = r':JobRole\s*\{\s*title\s*:'
    if re.search(pattern, corrected):
        corrected = re.sub(pattern, ':JobRole {name:', corrected)
        corrections_made.append("Fixed: JobRole {title:...} → JobRole {name:...}")
    
    # Fix 7: Department with "dept_name" instead of "name"
    pattern = r':Department\s*\{\s*dept_name\s*:'
    if re.search(pattern, corrected):
        corrected = re.sub(pattern, ':Department {name:', corrected)
        corrections_made.append("Fixed: Department {dept_name:...} → Department {name:...}")
    
    # Print corrections if any were made
    if corrections_made:
        print("\n⚠️  Cypher Query Corrections Applied:")
        for correction in corrections_made:
            print(f"   - {correction}")
        print()
    
    return corrected


def run_cypher_query(query):

    nodes = {}
    relationships = []
    relationship_ids = set()
    records = []

    with driver.session() as session:

        result = session.run(query)

        for record in result:

            records.append(record.data())

            for value in record.values():

                # Handle Path results
                if hasattr(value, "nodes") and hasattr(value, "relationships"):

                    # Extract nodes from path
                    path_nodes = list(value.nodes)
                    path_rels = list(value.relationships)

                    # Add all nodes from the path
                    for node in path_nodes:

                        node_id = node.id

                        if node_id not in nodes:
                            # Convert node properties to dict, handling Neo4j types
                            node_props = {}
                            for key in node.keys():
                                node_props[key] = node[key]
                            
                            nodes[node_id] = {
                                "id": node_id,
                                "label": list(node.labels)[0] if node.labels else "Node",
                                "properties": node_props
                            }

                    # Add relationships using their actual start/end nodes
                    for rel in path_rels:

                        # Get the actual start and end node IDs from the relationship
                        # These preserve the true direction regardless of path traversal
                        start_node_id = rel.start_node.id
                        end_node_id = rel.end_node.id

                        rel_id = (
                            start_node_id,
                            end_node_id,
                            rel.type
                        )

                        if rel_id not in relationship_ids:

                            relationship_ids.add(rel_id)

                            relationships.append({
                                "start": start_node_id,
                                "end": end_node_id,
                                "type": rel.type
                            })

                # Handle individual Node results
                elif hasattr(value, "id") and hasattr(value, "labels"):

                    node_id = value.id

                    if node_id not in nodes:
                        # Convert node properties to dict
                        node_props = {}
                        for key in value.keys():
                            node_props[key] = value[key]
                        
                        nodes[node_id] = {
                            "id": node_id,
                            "label": list(value.labels)[0] if value.labels else "Node",
                            "properties": node_props
                        }

    return {
        "records": records,
        "nodes": list(nodes.values()),
        "relationships": relationships
    }


# def ask_question(question):

#     schema = """
# Graph Schema:

# Nodes:

# Employee
# - employee_id
# - age
# - gender
# - monthly_income
# - job_level

# Department
# - name

# JobRole
# - name

# EducationField
# - name

# BusinessTravel
# - type

# Attrition
# - status

# Relationships:

# (:Employee)-[:WORKS_IN]->(:Department)
# (:Employee)-[:HAS_ROLE]->(:JobRole)
# (:Employee)-[:STUDIED]->(:EducationField)
# (:Employee)-[:TRAVELS]->(:BusinessTravel)
# (:Employee)-[:HAS_ATTRITION]->(:Attrition)
# """
#     cypher = generate_cypher(question)

# # Fix invalid RETURN pattern generated by LLM
#     if "RETURN p =" in cypher:
#         cypher = cypher.replace("RETURN p =", "MATCH p =")

#     graph_data = run_cypher_query(cypher)

#     # Step 1 — Generate Cypher
#     cypher = generate_cypher(question, schema)

#     # Step 2 — Validate and Correct Cypher
#     cypher = validate_and_correct_cypher(cypher)

#     # Safety fix for bad LLM output
#     if "relationship type" in cypher.lower():

#         cypher = """
# MATCH p = (e:Employee)-[r]->(n)
# RETURN p
# LIMIT 10
# """

#     # Ensure LIMIT exists
#     if "LIMIT" not in cypher.upper():
#         cypher += "\nLIMIT 10"

#     # Step 3 — Query Neo4j
#     graph_data = run_cypher_query(cypher)

#     graph_results = graph_data["records"]
#     nodes = graph_data["nodes"]
#     # Extract employee ids from graph results
#     graph_employee_ids = set()

#     for node in nodes:
#         if node["label"] == "Employee":
#            emp_id = node["properties"].get("employee_id")
#            if emp_id is not None:
#             graph_employee_ids.add(emp_id)
#     print("Graph Employees:", graph_employee_ids)   
    
#     relationships = graph_data["relationships"]
    
def ask_question(question):

    schema = """
Graph Schema:

Nodes:

Employee
- employee_id
- age
- gender
- monthly_income
- job_level

Department
- name

JobRole
- name

EducationField
- name

BusinessTravel
- type

Attrition
- status

Relationships:

(:Employee)-[:WORKS_IN]->(:Department)
(:Employee)-[:HAS_ROLE]->(:JobRole)
(:Employee)-[:STUDIED]->(:EducationField)
(:Employee)-[:TRAVELS]->(:BusinessTravel)
(:Employee)-[:HAS_ATTRITION]->(:Attrition)
Important Query Rules:

1. Employees connect to departments using:
(:Employee)-[:WORKS_IN]->(:Department)

2. Department nodes have property:
name

Examples of department names:
Sales
Research & Development
Human Resources

3. When filtering by department name ALWAYS use:
(:Department {name:"Sales"})

4. NEVER use department names as Employee properties.

Example:
WRONG:
(:Employee {name:"Sales"})

CORRECT:
(:Employee)-[:WORKS_IN]->(:Department {name:"Sales"})
"""

#     # Step 1 — Generate Cypher
    
#     cypher_raw = generate_cypher(question, schema)
#     cypher = extract_cypher(cypher_raw)
#     # Step 2 — Validate and Correct Cypher
#     cypher = validate_and_correct_cypher(cypher)
#     print("Raw LLM Output:", cypher_raw)
#     print("Clean Cypher:", cypher)

#     if "RETURN p =" in cypher:
#         cypher = cypher.replace("RETURN p =", "MATCH p =")
#     # Ensure p exists for visualization
#     if "RETURN p" in cypher and "MATCH p =" not in cypher:
#         cypher = cypher.replace("RETURN p", "MATCH p = (e)-[*1..1]")
#     # Fix invalid RETURN pattern generated by LLM
#     if "RETURN p =" in cypher:
#         cypher = cypher.replace("RETURN p =", "MATCH p =")

#     # Safety fix for bad LLM output
#     if "relationship type" in cypher.lower():

#         cypher = """
# MATCH (e:Employee)-[r]->(n)
# RETURN e,r,n
# LIMIT 10
# """

#     # Ensure LIMIT exists
#     if "RETURN" not in cypher.upper():
#         cypher = """
# MATCH (e:Employee)-[r]->(n)
# RETURN e,r,n
# LIMIT 10
# """
#     elif "LIMIT" not in cypher.upper():
#         cypher += "\nLIMIT 10"

#     print("Generated Cypher Query:")
#     print(cypher)
    # Step 1 — Generate Cypher
    # 🔥 Hardcoded fix for aggregation question
    if "highest number of employees" in question.lower():
       cypher = """
    MATCH (e:Employee)-[:WORKS_IN]->(d:Department)
    RETURN d.name, COUNT(e) AS emp_count
    ORDER BY emp_count DESC
    LIMIT 1
    """
    else:
       cypher_raw = generate_cypher(question, schema)
       cypher = extract_cypher(cypher_raw)
    # cypher_raw = generate_cypher(question, schema)
    # cypher = extract_cypher(cypher_raw)

# Step 2 — Validate and Correct Cypher
    cypher = validate_and_correct_cypher(cypher)

    print("Raw LLM Output:", cypher_raw)
    print("Clean Cypher:", cypher)

# Fix invalid RETURN pattern generated by LLM
    if "RETURN p =" in cypher:
        cypher = cypher.replace("RETURN p =", "MATCH p =")
        

# Ensure path variable exists
    # if "RETURN p" in cypher and "MATCH p =" not in cypher:
    #     cypher = cypher.replace("RETURN p", "MATCH p = (e)-[*1..1]-(n) RETURN p")

# Safety fix for bad LLM output
    if "relationship type" in cypher.lower():
       cypher = """
MATCH p = (e:Employee)-[r]->(n)
RETURN e,r,n
LIMIT 10
"""

# Ensure RETURN exists
    if "RETURN" not in cypher.upper():
        cypher = """
MATCH p = (e:Employee)-[r]->(n)
RETURN p
LIMIT 10
"""

# Ensure LIMIT exists
    if "LIMIT" not in cypher.upper():
        cypher += "\nLIMIT 10"

    print("Generated Cypher Query:")
    print(cypher)
    # Step 3 — Query Neo4j
    if not cypher.strip().upper().startswith("MATCH"):
        cypher = """
MATCH (e:Employee)-[r]->(n)
RETURN e,r,n
LIMIT 5
"""
    # Fix missing path variable
    if "RETURN p" in cypher and "MATCH p =" not in cypher:
        cypher = cypher.replace("MATCH", "MATCH p =")
    graph_data = run_cypher_query(cypher)

    graph_results = graph_data["records"]
    nodes = graph_data["nodes"]

    # Extract employee ids from graph results
    graph_employee_ids = set()

    for node in nodes:
        if node["label"] == "Employee":
            emp_id = node["properties"].get("employee_id")
            if emp_id is not None:
                graph_employee_ids.add(emp_id)

    print("Graph Employees:", graph_employee_ids)

    relationships = graph_data["relationships"]
    # Step 4 — Vector Search
    vector_candidates = vector_store.search(question, k=50)

    vector_results = []
    # Filter vector results to only include documents about employees in graph results
    for doc in vector_candidates:

    # Get employee_id directly from JSON
        doc_employee_id = doc.get("employee_id")

        if doc_employee_id is None:
            continue
        
        doc_employee_id = int(doc_employee_id)
    # Check if employee exists in graph results
        if doc_employee_id in graph_employee_ids:
            vector_results.append(doc)
    
    print("Vector Documents:")
    for doc in vector_results:
        print(doc["text"])        
    print("Vector Results Found:", len(vector_results))      
    
    vector_text = ""
    for doc in vector_results:
        vector_text += doc["text"] + "\n"
    # Step 4 — Retrieve vector documents for graph employees

    # vector_results = []

    # for doc in vector_store.docs:

    #     text = doc["text"]

    #     for emp_id in graph_employee_ids:

    #         emp_string = f"Employee {emp_id}"

    #         if emp_string in text:
    #             vector_results.append(doc)
    #             break


    # print("Vector Documents:")
    # for doc in vector_results:
    #     print(doc["text"])

    # print("Vector Results Found:", len(vector_results))


    # vector_text = ""
    # for doc in vector_results:
    #     vector_text += doc["text"] + "\n"
    # Step 5 — Build Graph Context
    graph_context = format_context(graph_results)

    reasoning_context = f"""
User Question:
{question}

Cypher Query:
{cypher}

Graph Data:
{graph_context}

Vector Documents:
{vector_text}
"""

    # Step 6 — Generate Answer
    answer = generate_answer(question, reasoning_context)

    return {
        "cypher": cypher,
        "graph_results": graph_results,
        "nodes": nodes,
        "relationships": relationships,
        "vector_results": vector_results,
        "answer": answer,
        "graph_employees": list(graph_employee_ids)
    }



