import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate"


def call_llm(prompt):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]


def extract_cypher(llm_response: str) -> str:
    """
    Safely extract only Cypher query from LLM output.
    """


    # Remove only the backtick markers, NOT the content
    llm_response = llm_response.replace("```", "")
    llm_response = llm_response.replace("cypher", "")

    # Remove common unwanted phrases
    llm_response = llm_response.replace("Here is the corrected query:", "")
    llm_response = llm_response.replace("Corrected query:", "")

    # Find valid Cypher start
    pattern = r"(MATCH|OPTIONAL MATCH|WITH|CALL).*"

    match = re.search(pattern, llm_response, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(0).strip()

    raise Exception("No valid Cypher found in LLM output")
