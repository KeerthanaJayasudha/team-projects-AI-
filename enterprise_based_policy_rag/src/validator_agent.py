"""
Agent 3 — Answer Validator (Lightweight, no LLM call)
Checks answer grounding against retrieved context using
token overlap and key phrase matching. Fast and deterministic.
"""

import re
from src.logger import get_logger

logger = get_logger(__name__)


def _tokenize(text: str) -> set:
    """Lowercase word tokens, strip punctuation."""
    return set(re.findall(r'\b[a-z]{3,}\b', text.lower()))

_HALLUCINATION_PHRASES = [
    "as an ai", "i don't have access", "i cannot find",
    "not mentioned", "not specified", "no information",
    "based on my knowledge", "according to my training",
    "i believe", "i think", "probably", "it is likely",
    "you should consult", "i am not sure",
]

_REFUSAL_PHRASES = [
    "refused", "no policy found", "cannot answer",
    "not in the context", "not provided"
]


def validate_answer(answer: str, context: str, question: str) -> dict:
    logger.info("[ValidatorAgent] Validating answer grounding...")

    answer_lower  = answer.lower()
    context_lower = context.lower()

    # ── Check 1: Detect outright refusal phrases ──
    for phrase in _REFUSAL_PHRASES:
        if phrase in answer_lower:
            return {
                "valid":   False,
                "verdict": "HALLUCINATED",
                "reason":  "Answer contains refusal — not grounded in context."
            }

    # ── Check 2: Detect hallucination signal phrases ──
    for phrase in _HALLUCINATION_PHRASES:
        if phrase in answer_lower:
            return {
                "valid":   False,
                "verdict": "HALLUCINATED",
                "reason":  f"Answer contains out-of-context phrase: '{phrase}'"
            }

    # ── Check 3: Token overlap between answer and context ──
    answer_tokens  = _tokenize(answer)
    context_tokens = _tokenize(context)

    if not answer_tokens:
        return {"valid": False, "verdict": "HALLUCINATED", "reason": "Empty answer."}

    overlap      = answer_tokens & context_tokens
    overlap_ratio = len(overlap) / len(answer_tokens)

    logger.info(
        f"[ValidatorAgent] Token overlap: {len(overlap)}/{len(answer_tokens)} "
        f"= {round(overlap_ratio, 2)}"
    )

    # ── Verdict thresholds ──
    if overlap_ratio >= 0.45:
        verdict = "GROUNDED"
        valid   = True
        reason  = f"Answer well-grounded ({round(overlap_ratio*100)}% token overlap with context)."
    elif overlap_ratio >= 0.25:
        verdict = "PARTIAL"
        valid   = True
        reason  = f"Answer partially grounded ({round(overlap_ratio*100)}% overlap — minor extrapolation possible)."
    else:
        verdict = "HALLUCINATED"
        valid   = False
        reason  = f"Low overlap ({round(overlap_ratio*100)}%) — answer may not be grounded in retrieved context."

    logger.info(f"[ValidatorAgent] Verdict: {verdict} | {reason}")
    return {"valid": valid, "verdict": verdict, "reason": reason}