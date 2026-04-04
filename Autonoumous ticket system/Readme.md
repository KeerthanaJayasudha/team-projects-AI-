Overview
The AI Ticket Triage System automatically classifies, prioritizes, and routes IT support tickets using semantic search and rule-based logic.


Architecture

Frontend (React) → Backend (FastAPI) → Embeddings → FAISS → Rule Engine + RAG → Output

 Tech Stack

- Frontend: React + Tailwind CSS  
- Backend: FastAPI  
- Embeddings: Sentence Transformers  
- Vector DB: FAISS  
- AI Approach: Retrieval-Augmented Generation (RAG)

Features

- Ticket classification (Network, Software, etc.)
- Priority assignment (P1–P4)
- Suggested resolution using past tickets
- Confidence-based decision making
- Automatic escalation for critical/uncertain cases

Input

- Ticket Title  
- Description  
- User Role  

Output

- Category  
- Priority  
- Suggested Resolution  
- Confidence Score  
- Escalation Decision  


 Decision Rules

Classification
- Uses semantic similarity via FAISS  
- Assigns category based on closest match  

CATEGORIES = [
    "Access Issue",
    "Network Issue",
    "Email Service",
    "Database Error",
    "Deployment Issue",
    "Security Issue",
    "Performance Issue",
    "Hardware Issue",
    "Software Bug"
]

Priority
P1 Conditions
- "server down"
- "system outage"
- "database failure"
- "production issue"
P2 Conditions
- VPN issues
- Email not working
- Network slow
P3 Conditions
- Individual user issue
- App bug
P4 Conditions
- Feature request
- Minor inconvenience  

Confidence
- > 0.80 → High  
- 0.60–0.80 → Medium  
- < 0.60 → Low  

Escalation
Escalation = YES when:

1. Priority = P1
2. Confidence < 0.6
3. No matching solution found

Escalation = NO when:

1. Priority = P2/P3/P4
2. Confidence is high
3. Solution exists


 Workflow

1. User submits ticket  
2. Text converted to embeddings  
3. Similar tickets retrieved  
4. Category & priority assigned  
5. Resolution suggested (RAG)  
6. Confidence calculated  
7. Escalation decision made  
