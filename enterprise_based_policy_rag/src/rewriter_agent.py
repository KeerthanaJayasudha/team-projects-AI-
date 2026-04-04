"""
Agent 2 — Query Rewriter (Rule-based, no LLM call)
Expands slang, abbreviations, and vague terms into
retrieval-optimised policy language using pattern matching.
"""

import re
from src.logger import get_logger

logger = get_logger(__name__)

# Slang / informal → formal policy language
_REPLACEMENTS = [
    (r'\bi\b',                    'users'),
    (r'\bmy\b',                   'their'),
    (r'\bme\b',                   'users'),
    (r'\bcan i\b',                'are users permitted to'),
    (r'\bam i allowed\b',         'are users permitted to'),
    (r'\bis it ok\b',             'is it permitted to'),
    (r'\bget caught\b',           'be found in violation'),
    (r'\bget in trouble\b',       'face disciplinary action'),
    (r'\bget fired\b',            'be terminated for'),
    (r'\bwhat happens if\b',      'what are the consequences if'),
    (r'\bwhat if\b',              'what are the consequences if'),
    (r'\bpunishment\b',           'disciplinary sanctions'),
    (r'\bpenalty\b',              'disciplinary sanctions'),
    (r'\bban\b',                  'prohibition'),
    (r'\bbanned\b',               'prohibited'),
    (r'\bpass(word)?s?\b',        'passwords'),
    (r'\bpwd\b',                  'password'),
    (r'\blaptop\b',               'personal computing device'),
    (r'\bphone\b',                'mobile device'),
    (r'\bbyod\b',                 'bring your own device policy'),
    (r'\bai\b',                   'artificial intelligence'),
    (r'\bsocial media\b',         'social media usage'),
    (r'\bwork from home\b',       'remote working telework policy'),
    (r'\bwfh\b',                  'remote working telework policy'),
    (r'\bgames?\b',               'personal recreational activities'),
    (r'\bporn\b',                 'sexually explicit content'),
    (r'\bhack\b',                 'unauthorized access'),
    (r'\bspy\b',                  'unauthorized monitoring'),
    (r'\bsteal\b',                'unauthorized access to'),
    (r'\bshare (my )?password\b', 'disclose authentication credentials'),
    (r'\bfire(arms?)?\b',         'firearms weapons campus policy'),
    (r'\bgun\b',                  'firearm weapon campus policy'),
    (r'\bconflict of interest\b', 'financial conflict of interest disclosure'),
]

_ALREADY_FORMAL = re.compile(
    r'\b(policy|regulation|compliance|permitted|prohibited|sanctions|'
    r'disciplinary|disclosure|investigator|acceptable use|procedure)\b',
    re.IGNORECASE
)


def rewrite_query(question: str) -> dict:
    logger.info(f"[RewriterAgent] Original: \"{question}\"")

    # If already formal policy language — pass through unchanged
    if _ALREADY_FORMAL.search(question) and len(question.split()) >= 6:
        logger.info("[RewriterAgent] Already formal — no rewrite needed.")
        return {"rewritten": question, "changed": False}

    rewritten = question.lower().strip()

    for pattern, replacement in _REPLACEMENTS:
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

    # Capitalise first letter
    rewritten = rewritten.strip().capitalize()

    changed = rewritten.lower() != question.lower()
    logger.info(f"[RewriterAgent] Rewritten: \"{rewritten}\" | Changed: {changed}")

    return {"rewritten": rewritten, "changed": changed}