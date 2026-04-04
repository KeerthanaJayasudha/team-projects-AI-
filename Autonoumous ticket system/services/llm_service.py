import ollama
import json
import re

from config import OLLAMA_MODEL, CATEGORIES


def extract_json(text):

    text = text.replace("```json", "").replace("```", "")

    match = re.search(r'\{.*\}', text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group())
        except:
            return None

    return None


def get_llm_decision(ticket_text, similar_tickets):

    prompt = f"""
You are an AI IT ticket triage assistant.

Choose the category ONLY from this list:

{CATEGORIES}

Use the historical tickets as reference.

New Ticket:
{ticket_text}

Similar Tickets:
{similar_tickets}

Return ONLY JSON:

{{
"category": "...",
"priority": "P1/P2/P3/P4",
"suggested_resolution": "...",
"escalation_required": true or false
}}
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    output = response["message"]["content"]

    decision = extract_json(output)

    if decision is None:
        decision = {
            "category": "Access Issue",
            "priority": "P3",
            "suggested_resolution": "Manual review required",
            "escalation_required": False
        }

    return decision