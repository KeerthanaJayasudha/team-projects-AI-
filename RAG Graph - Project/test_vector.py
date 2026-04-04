from vector_store import VectorStore

vector_db = VectorStore("employee_docs.json")

query = "Sales employees"

results = vector_db.search(query)

print("\nVector Search Results:\n")

for r in results:
    print(r["text"])
