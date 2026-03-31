import requests

def generate_answer(question, context):

    prompt = f"""
You are a Graph-RAG HR analytics assistant.

Use ONLY the graph results below to answer.

Question:
{question}

Graph Results:
{context}


Provide a clear human-readable answer in plain text.

Important:
- If the query results were limited (e.g., LIMIT 5), do NOT say "in total".
- Instead say: "The query returned X records (limited by the query constraint)."
- Only describe what is actually returned in the Graph Results.
- Do NOT assume the full dataset size.

"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()
    return result["response"]

