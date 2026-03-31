"""
Agent 1 — Intent Classifier (Rule-based, no LLM call)
Fast keyword + pattern matching instead of LLM inference.
"""

import re
from src.logger import get_logger

logger = get_logger(__name__)

INTENT_GREETING    = "GREETING"
INTENT_OOB         = "OUT_OF_SCOPE"
INTENT_POLICY      = "POLICY"
INTENT_UNCLEAR     = "UNCLEAR"

GREETING_RESPONSES = {
    INTENT_GREETING: (
        "Hello! I'm the Enterprise Policy Q&A Assistant. "
        "I can answer questions about IT, security, compliance, and acceptable use policies. "
        "What would you like to know?"
    ),
    INTENT_OOB: (
        "I'm a policy assistant — I can only answer questions grounded in "
        "official enterprise policy documents (IT, HR, Security, Compliance). "
        "Please ask a policy-related question."
    ),
    INTENT_UNCLEAR: (
        "I didn't quite understand that. Could you rephrase your question? "
        "I can help with IT policies, acceptable use, security guidelines, and compliance rules."
    ),
}

_GREETINGS = {
    "hi", "hello", "hey", "howdy", "greetings", "sup", "yo",
    "good morning", "good afternoon", "good evening",
    "how are you", "how r u", "thanks", "thank you", "ty",
    "bye", "goodbye", "see you", "cheers"
}

_OOB_KEYWORDS = {
    "weather", "sport", "football", "cricket", "movie", "film",
    "music", "song", "recipe", "cook", "stock", "price",
    "joke", "funny", "news", "politics", "election",
    "covid", "vaccine", "game", "play", "travel"
}

_POLICY_KEYWORDS = {
    "policy", "policies", "rule", "rules", "regulation", "compliance",
    "password", "passwords", "email", "internet", "network", "vpn",
    "data", "privacy", "security", "access", "permission", "allowed",
    "prohibited", "banned", "restrict", "enforce", "violation",
    "acceptable", "use", "software", "hardware", "device", "byod",
    "firearm", "weapon", "campus", "conflict", "interest", "disclosure",
    "harassment", "report", "incident", "install", "download",
    "confidential", "encrypt", "monitor", "ai", "social media",
    "remote", "telework", "disciplinary", "sanction", "penalty",
    "research", "investigator", "financial", "employee", "faculty",
    "student", "staff", "login", "account", "credential", "share",
    "personal", "information", "copyright", "license", "piracy"
}


def classify_intent(question: str) -> dict:
    q = question.strip().lower()
    q_clean = re.sub(r'[^\w\s]', '', q)
    words = set(q_clean.split())

    logger.info(f"[IntentAgent] Classifying: \"{question}\"")

    # 1 — Greeting check (exact short phrase or known greeting words)
    if q_clean in _GREETINGS or words <= _GREETINGS or len(words) <= 2 and words & _GREETINGS:
        logger.info("[IntentAgent] Intent: GREETING")
        return {"intent": INTENT_GREETING, "response": GREETING_RESPONSES[INTENT_GREETING]}

    # 2 — Out-of-scope check
    if words & _OOB_KEYWORDS and not words & _POLICY_KEYWORDS:
        logger.info("[IntentAgent] Intent: OUT_OF_SCOPE")
        return {"intent": INTENT_OOB, "response": GREETING_RESPONSES[INTENT_OOB]}

    # 3 — Policy check (any policy keyword or question about rules/can I/am I allowed)
    policy_patterns = [
        r'\b(can|may|should|must|is it|are|what|how|when|why|who|does|do)\b',
        r'\b(allow|permit|prohibit|restrict|require|mandate)\w*\b',
    ]
    has_question = any(re.search(p, q) for p in policy_patterns)
    has_policy_word = bool(words & _POLICY_KEYWORDS)

    if has_policy_word or (has_question and len(words) >= 4):
        logger.info("[IntentAgent] Intent: POLICY")
        return {"intent": INTENT_POLICY, "response": None}

    # 4 — Too short or vague
    if len(words) <= 2:
        logger.info("[IntentAgent] Intent: UNCLEAR")
        return {"intent": INTENT_UNCLEAR, "response": GREETING_RESPONSES[INTENT_UNCLEAR]}

    # Default — treat as policy (safe)
    logger.info("[IntentAgent] Intent: POLICY (default)")
    return {"intent": INTENT_POLICY, "response": None}