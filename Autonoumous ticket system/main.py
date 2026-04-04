from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.rag_service import retrieve_similar_tickets
from services.llm_service import get_llm_decision
from services.rule_engine import apply_rules
from services.notification_service import send_escalation_email

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TicketRequest(BaseModel):
    title: str
    description: str
    user_role: str

@app.post("/triage")
def triage(ticket: TicketRequest):
    try:
        ticket_text = ticket.title + " " + ticket.description

        # 🔥 RAG
        rag_data = retrieve_similar_tickets(ticket_text)

        # 🔥 LLM
        decision = get_llm_decision(ticket_text, rag_data["tickets"])

        # 🔥 Confidence
        scores = rag_data["similarity_scores"]
        decision["confidence"] = float(max(scores)) if scores else 0.0

        # 🔥 Apply intelligent rules
        decision = apply_rules(decision, rag_data, ticket.user_role, ticket_text)

        # 🔥 Email escalation
        if decision["escalation_required"]:
            send_escalation_email(
                title=ticket.title,
                description=ticket.description,
                decision=decision,
                user_role=ticket.user_role
            )

        # ✅ SAFE RESPONSE
        return {
            "category": decision.get("category"),
            "priority": decision.get("priority"),
            "suggested_resolution": decision.get("suggested_resolution"),
            "escalation_required": decision.get("escalation_required"),
            "confidence": float(decision.get("confidence", 0))
        }

    except Exception as e:
        return {"error": str(e)}