
# import streamlit as st
# from rag_pipeline import ask_question
# from pyvis.network import Network
# import streamlit.components.v1 as components

# st.set_page_config(
#     page_title="Employee Knowledge Graph Assistant",
#     page_icon="🧠",
#     layout="wide"
# )

# st.markdown("""
# # 🧠 Employee Knowledge Graph Assistant
# Ask questions about employee data using **Graph RAG with Neo4j + Vector Search**
# """)

# question = st.text_input(
#     "Ask a question about employees",
#     placeholder="Example: Show employees in the Sales department"
# )

# if st.button("Get Answer"):

#     if question:

#         with st.spinner("Running Graph RAG pipeline..."):
#             result = ask_question(question)
#             col1, col2 = st.columns(2)

#         # -----------------------------
#         # Step 1 — Show Cypher Query
#         # -----------------------------
#         st.subheader("Generated Cypher Query")
#         st.code(result["cypher"], language="cypher")

#         # -----------------------------
#         # Step 2 — Show Graph Results
#         # -----------------------------
#         st.subheader("Graph Query Results")

#         graph_results = result["graph_results"]
           

# #         for record in graph_results:

# #             if "p" in record:

# #                 path = record["p"]

# #                 start_node = path[0]
# #                 relationship = path[1]
# #                 end_node = path[2]

# #                 # # employee_id = start_node.get("employee_id", "Unknown")

# #                 # # if relationship == "WORKS_IN":
# #                 # #     dept = end_node.get("name", "")
# #                 # #     st.write(f"Employee {employee_id} works in {dept} department.")

# #                 # elif relationship == "HAS_ROLE":
# #                 #     role = end_node.get("name", "")
# #                 #     st.write(f"Employee {employee_id} has role {role}.")

# #                 # elif relationship == "STUDIED":
# #                 #     field = end_node.get("name", "")
# #                 #     st.write(f"Employee {employee_id} studied {field}.")

# #                 # elif relationship == "TRAVELS":
# #                 #     travel = end_node.get("type", "")
# #                 #     st.write(f"Employee {employee_id} travels {travel}.")

# #                 # elif relationship == "HAS_ATTRITION":
# #                 #     status = end_node.get("status", "")
# #                 #     st.write(f"Employee {employee_id} attrition status is {status}.")
# #                 seen = set()
# #                 employee_id = start_node.get("employee_id", "Unknown")

# # # ✅ Skip duplicates
# #                 if employee_id in seen:
# #                     continue

# #                 seen.add(employee_id)

# #                 if relationship == "WORKS_IN":
# #                     dept = end_node.get("name", "")
# #                     st.write(f"Employee {employee_id} works in {dept} department.")

# #                 elif relationship == "HAS_ROLE":
# #                     role = end_node.get("name", "")
# #                     st.write(f"Employee {employee_id} has role {role}.")

# #                 elif relationship == "STUDIED":
# #                     field = end_node.get("name", "")
# #                     st.write(f"Employee {employee_id} studied {field}.")

# #                 elif relationship == "TRAVELS":
# #                     travel = end_node.get("type", "")
# #                     st.write(f"Employee {employee_id} travels {travel}.")

# #                 elif relationship == "HAS_ATTRITION":
# #                     status = end_node.get("status", "")
# #                     st.write(f"Employee {employee_id} attrition status is {status}.")

#         # -----------------------------
#         # # Step 3 — Graph Visualization
#         # # -----------------------------
#         # st.subheader("Graph Visualization")

#         # nodes = result.get("nodes", [])
#         # relationships = result.get("relationships", [])

#         # if len(nodes) == 0:
#         #     st.warning("No graph data returned from Neo4j.")

#         # else:

#         #     net = Network(
#         #         height="600px",
#         #         width="100%",
#         #         directed=True,
#         #         bgcolor="#222222",
#         #         font_color="white"
#         #     )

#         #     net.barnes_hut(
#         #         gravity=-3000,
#         #         central_gravity=0.3,
#         #         spring_length=200,
#         #         spring_strength=0.05,
#         #         damping=0.09
#         #     )

#         #     label_colors = {
#         #         "Employee": "#F4A261",
#         #         "Department": "#8AB6C1"
#         #     }

#         #     for node in nodes:

#         #         node_id = str(node["id"])
#         #         label = node.get("label", "Node")
#         #         props = node.get("properties", {})

#         #         if label == "Employee":
#         #             node_name = props.get("employee_id", node_id)

#         #         elif label == "Department":
#         #             node_name = props.get("name", node_id)

#         #         elif label == "JobRole":
#         #             node_name = props.get("name", node_id)

#         #         elif label == "EducationField":
#         #             node_name = props.get("name", node_id)

#         #         elif label == "BusinessTravel":
#         #             node_name = props.get("type", node_id)

#         #         elif label == "Attrition":
#         #             node_name = props.get("status", node_id)

#         #         else:
#         #             node_name = props.get("name") or props.get("employee_id") or node_id

#         #         color = label_colors.get(label, "#90CAF9")

#         #         net.add_node(
#         #             node_id,
#         #             label=str(node_name),
#         #             title=str(props),
#         #             color=color,
#         #             size=30
#         #         )

#         #     for rel in relationships:

#         #         net.add_edge(
#         #             str(rel["start"]),
#         #             str(rel["end"]),
#         #             label=rel["type"],
#         #             arrows="to"
#         #         )

#         #     net.save_graph("graph.html")

#         #     HtmlFile = open("graph.html", "r", encoding="utf-8")
#         #     components.html(HtmlFile.read(), height=600)

#         # -----------------------------
#         # Step 4 — Vector Results
#         # -----------------------------
#         st.subheader("Vector Search Results")

#         for doc in result["vector_results"]:
#             st.write(doc["text"])

#         # -----------------------------
#         # Step 5 — Final Answer
#         # -----------------------------
#         st.subheader("Final Graph-RAG Answer")
#         st.success(result["answer"])

import streamlit as st
from rag_pipeline import ask_question

st.set_page_config(
    page_title="Employee Knowledge Graph Assistant",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
# 🧠 Employee Knowledge Graph Assistant
Ask questions about employee data using **Graph RAG with Neo4j + Vector Search**
""")

question = st.text_input(
    "Ask a question about employees",
    placeholder="Example: Show employees in the Sales department"
)

if st.button("Get Answer"):

    if question:

        with st.spinner("Running Graph RAG pipeline..."):
            result = ask_question(question)

        # -----------------------------
        # Step 1 — Show Cypher Query
        # -----------------------------
        st.subheader("Generated Cypher Query")
        st.code(result["cypher"], language="cypher")

        # -----------------------------
        # Step 2 — Show CLEAN Graph Results ✅
        # -----------------------------
        st.subheader("Graph Employees (Clean Output)")

        if "graph_employees" in result and result["graph_employees"]:

            for emp_id in result["graph_employees"]:
                st.write(f"Employee {emp_id} works in Sales department.")

        else:
            st.warning("No employee results found.")

        # -----------------------------
        # Step 3 — Vector Results
        # -----------------------------
        st.subheader("Vector Search Results")

        if result["vector_results"]:
            for doc in result["vector_results"]:
                st.write(doc["text"])
        else:
            st.info("No matching vector documents found.")

        # -----------------------------
        # Step 4 — Final Answer
        # -----------------------------
        st.subheader("Final Graph-RAG Answer")
        st.success(result["answer"])
