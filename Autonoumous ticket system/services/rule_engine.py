from collections import Counter
from services.embedding_service import generate_embedding
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------
# BASIC RULE PRIORITY
# -----------------------------
def assign_priority(text: str) -> str:
    text = text.lower()

    if any(k in text for k in [
        "server down", "outage", "data loss",
        "security breach", "unauthorized", "hacked"
    ]):
        return "P1"

    elif any(k in text for k in [
        "vpn", "login", "email not working", "cannot connect"
    ]):
        return "P2"

    elif any(k in text for k in [
        "slow", "error", "bug", "delay", "crash"
    ]):
        return "P3"

    return "P4"


# -----------------------------
# 🔥 SEMANTIC CRITICAL DETECTION
# -----------------------------
CRITICAL_PATTERNS = [
    "system outage",
    "production failure",
    "payment failure",
    "transactions failing",
    "security breach",
    "unauthorized access",
    "account hacked",
    "data loss"
]

def semantic_critical_detection(text):
    text_emb = generate_embedding(text)

    for pattern in CRITICAL_PATTERNS:
        pattern_emb = generate_embedding(pattern)

        score = cosine_similarity(
            [text_emb], [pattern_emb]
        )[0][0]

        if score > 0.65:
            return "P1"

    return None


# -----------------------------
# ROLE ADJUSTMENT (FIXED)
# -----------------------------
def adjust_priority_by_role(priority: str, user_role: str) -> str:

    if user_role in ["CEO", "CTO", "Director"]:
        if priority == "P3":
            return "P2"

    if user_role == "IT Admin" and priority == "P3":
        return "P2"

    return priority


# -----------------------------
# RAG PRIORITY (MAJORITY)
# -----------------------------
def get_rag_priority(priorities):
    if not priorities:
        return "P3"

    count = Counter(priorities)
    return count.most_common(1)[0][0]


# -----------------------------
# WEIGHTED FUSION
# -----------------------------
def weighted_priority(rule_p, llm_p, rag_p):

    weights = {
        "rule": 0.4,
        "llm": 0.4,
        "rag": 0.2
    }

    score_map = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}

    total = (
        score_map[rule_p] * weights["rule"] +
        score_map[llm_p] * weights["llm"] +
        score_map[rag_p] * weights["rag"]
    )

    if total <= 1.5:
        return "P1"
    elif total <= 2.5:
        return "P2"
    elif total <= 3.5:
        return "P3"
    else:
        return "P4"


# -----------------------------
# FINAL APPLY RULES
# -----------------------------
def apply_rules(decision, rag_data, user_role, ticket_text):

    text = ticket_text

    # Step 1: Rule priority
    rule_p = assign_priority(text)

    # Step 2: LLM priority
    llm_p = decision.get("priority", "P3")

    # Step 3: Semantic critical override 🔥
    semantic_p = semantic_critical_detection(text)

    # Step 4: RAG priority (only if confident)
    similarity_scores = rag_data["similarity_scores"]
    high_conf = max(similarity_scores) > 0.7 if similarity_scores else False

    if high_conf:
        rag_p = get_rag_priority(rag_data["priorities"])
    else:
        rag_p = "P3"

    # Step 5: Weighted fusion
    final_priority = weighted_priority(rule_p, llm_p, rag_p)

    # Step 6: Semantic override
    if semantic_p == "P1":
        final_priority = "P1"

    # Step 7: RAG category boost
    if "System Outage" in rag_data.get("categories", []):
        final_priority = "P1"

    # Step 8: Role adjustment
    final_priority = adjust_priority_by_role(final_priority, user_role)

    decision["priority"] = final_priority

    # -----------------------------
    # 🔥 SMART ESCALATION
    # -----------------------------
    escalations = rag_data["escalations"]

    escalation_rate = (
        sum(escalations) / len(escalations)
        if escalations else 0
    )

    confidence = decision.get("confidence", 1)

    if final_priority == "P1":
        decision["escalation_required"] = True

    elif final_priority == "P2" and escalation_rate > 0.7:
        decision["escalation_required"] = True

    elif confidence < 0.3 and final_priority in ["P1", "P2"]:
        decision["escalation_required"] = True

    else:
        decision["escalation_required"] = False

    return decision