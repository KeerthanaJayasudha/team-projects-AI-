
"""
Graph RAG Pipeline:

User Question
    ↓
LLM → Cypher Generation
    ↓
Neo4j Graph Execution
    ↓
Graph Results
    ↓
Vector Search (Hybrid Retrieval)
    ↓
LLM Final Explanation
"""

from vector_store import VectorStore
from query_generator import generate_cypher
from neo4j_executor import Neo4jExecutor
from context_builder import format_context
from answer_generator import generate_answer
from llm_utils import call_llm
import re


# ----------------------------
# Neo4j Connection Details
# ----------------------------

URI = "bolt://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "neo4j123"

executor = Neo4jExecutor(URI, USERNAME, PASSWORD)


# ----------------------------
# Extract Only Cypher Query
# ----------------------------

def extract_cypher(text):

    lines = text.split("\n")

    cypher_lines = []

    for line in lines:

        line = line.strip()

        if line.startswith(("MATCH", "WITH", "CALL", "RETURN")):
            cypher_lines.append(line)

    return "\n".join(cypher_lines)


# ----------------------------
# Validate Relationships
# ----------------------------

def validate_cypher(query):

    ALLOWED_RELATIONSHIPS = [
        "WORKS_IN",
        "HAS_ATTRITION",
        "HAS_ROLE",
        "STUDIED",
        "TRAVELS"
    ]

    found_relationships = re.findall(r"\[:(\w+)\]", query)

    for rel in found_relationships:
        if rel not in ALLOWED_RELATIONSHIPS:
            print(f"\n❌ Invalid relationship detected: {rel}")
            return False

    return True


# ----------------------------
# Main Pipeline
# ----------------------------

def main():

    print("\n--- Graph RAG QA System (Hybrid Graph + Vector RAG) ---\n")

    vector_db = VectorStore("employee_docs.json")

    question = input("Ask your question: ")

    # Step 1 — Generate Cypher
    schema = executor.get_schema()

    raw_response = generate_cypher(question, schema)

    cypher_query = extract_cypher(raw_response)

    if not cypher_query:
        print("\n❌ Could not extract Cypher query.")
        return

    print("\nGenerated Cypher Query:\n")
    print(cypher_query)

    try:

        max_attempts = 3
        attempt = 0
        results = None

        while attempt < max_attempts:

            try:

                print(f"\nAttempt {attempt+1}")

                if not validate_cypher(cypher_query):
                    raise Exception("Invalid relationship detected")

                print("\nFinal Query Being Executed:\n", cypher_query)

                results = executor.run_query(cypher_query)

                break

            except Exception as e:

                attempt += 1

                print("\n⚠️ Query failed. Attempting automatic correction...\n")

                fix_prompt = f"""
You are a Neo4j Cypher expert.

Fix the Cypher query.

Rules:
- Return ONLY Cypher
- Do not explain anything
- Do not add extra text

Broken Query:
{cypher_query}

Error:
{str(e)}

Correct Query:
"""

                corrected_response = call_llm(fix_prompt)

                cypher_query = extract_cypher(corrected_response)

                print("\n🔁 Corrected Query:\n", cypher_query)

        if results is None:
            print("\n❌ Failed after max retries.")
            return

        if not results:
            print("\n⚠️ No results found.")
            return

        print("\n📊 Graph Query Results:\n")

        for row in results:
            print(row)

        # ----------------------------
        # Vector Retrieval
        # ----------------------------

        print("\n🔎 VECTOR SEARCH RESULTS:\n")

        vector_results = vector_db.search(question)

        vector_text = ""

        for doc in vector_results:

            print(doc["text"])

            vector_text += doc["text"] + "\n"

        # ----------------------------
        # Build Context
        # ----------------------------

        graph_context = format_context(results)

        reasoning_context = f"""
You are answering using both graph reasoning and document retrieval.

User Question:
{question}

Cypher Query Used:
{cypher_query}

Graph Data Retrieved:
{graph_context}

Related Documents:
{vector_text}

Explain the answer clearly.
"""

        # ----------------------------
        # Final LLM Answer
        # ----------------------------

        answer = generate_answer(question, reasoning_context)

        print("\n🧠 FINAL GRAPH-RAG ANSWER:\n")

        print(answer)

    except Exception as e:

        print("\n❌ Critical error:")

        print(e)

    finally:

        executor.driver.close()


if __name__ == "__main__":
    main()