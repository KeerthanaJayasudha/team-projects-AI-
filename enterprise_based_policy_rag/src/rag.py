import re
import os
from src.retriever import retrieve
from src.llm import get_llm
from src.config import RELEVANCE_THRESHOLD, RERANKER_TOP_N
from src.logger import get_logger
from src.intent_agent import classify_intent, INTENT_POLICY
from src.rewriter_agent import rewrite_query
from src.validator_agent import validate_answer
from langchain_core.prompts import ChatPromptTemplate

logger = get_logger(__name__)


# --------------------------------------------------
# Utility → clean context a bit before giving to LLM
# removes very small sentences which are usually noise
# --------------------------------------------------
def filter_sentences(context):
    sentences = re.split(r'(?<=[.!?])\s+', context)
    filtered = [s.strip() for s in sentences if len(s.strip()) >= 15]
    return "\n".join(filtered)


# --------------------------------------------------
# This function is responsible for final answer generation
# LLM is strictly forced to use only retrieved context
# --------------------------------------------------
def extract_answer(context, question):
    llm = get_llm()

    # simple controlled prompt to reduce hallucination
    prompt = ChatPromptTemplate.from_template("""
You are a policy assistant. Answer the question using ONLY the context provided below.

Rules:
- Answer using only information present in the Context.
- Be concise and direct.
- If the context contains a partial answer, still provide it.
- Only respond with REFUSED: No policy found if the Context contains absolutely no relevant information.

Context:
{context}

Question:
{question}

Answer:
""")

    chain = prompt | llm

    try:
        response = chain.invoke({"context": context, "question": question})
        return response.content.strip()
    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        return "REFUSED: No policy found"


# --------------------------------------------------
# Extract readable document names + page numbers
# used for showing citations in final output
# --------------------------------------------------
def extract_sources(metas):
    sources = []

    for meta in metas:
        if meta is None:
            continue

        source = meta.get("source", "Unknown Document")

        # clean file name → make it presentable
        source = os.path.basename(source)\
                    .replace("-", " ")\
                    .replace(".pdf", "")\
                    .title()

        page = meta.get("page")

        if page is not None:
            sources.append(f"{source} (Page {page + 1})")
        else:
            sources.append(source)

    return list(set(sources))


# --------------------------------------------------
# MAIN RAG FLOW
# Intent Agent → Query Rewrite → Retrieval → LLM → Validation
# --------------------------------------------------
def rag_answer(question):

    logger.info(f"Question received: \"{question}\"")
    agent_trace = []

    # ---------- Agent 1 : Intent detection ----------
    # decides whether question is policy related or general chat
    intent_result = classify_intent(question)
    intent = intent_result["intent"]

    agent_trace.append({
        "agent": "Intent Classifier",
        "input": question,
        "output": intent,
        "detail": f"Classified as: {intent}"
    })

    logger.info(f"[Agent 1] Intent: {intent}")

    # if not policy → skip heavy RAG pipeline and respond directly
    if intent != INTENT_POLICY:
        logger.info(f"[Agent 1] Non-policy — skipping RAG.")
        return {
            "answer": intent_result["response"],
            "sources": [],
            "confidence": None,
            "distance": None,
            "intent": intent,
            "rewritten": None,
            "validation": None,
            "agent_trace": agent_trace
        }

    # ---------- Agent 2 : Query rewriting ----------
    # improves search quality (expands vague questions etc.)
    rewrite_result = rewrite_query(question)
    search_query = rewrite_result["rewritten"]

    agent_trace.append({
        "agent": "Query Rewriter",
        "input": question,
        "output": search_query,
        "detail": f"Rewritten: {'Yes' if rewrite_result['changed'] else 'No'}"
    })

    logger.info(f"[Agent 2] Search query: \"{search_query}\"")

    # ---------- Vector retrieval ----------
    results = retrieve(search_query)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    scores = results["distances"][0]

    # nothing retrieved → hard refusal
    if not docs:
        logger.warning("No documents returned from retrieval.")
        return {
            "answer": "REFUSED: No policy found",
            "sources": [],
            "confidence": 0,
            "distance": None,
            "intent": intent,
            "rewritten": search_query,
            "validation": None,
            "agent_trace": agent_trace
        }

    # results already reranked inside retriever using cross-encoder
    best_score = scores[0]

    logger.info(
        f"Best distance (post-rerank): {round(best_score,3)} | "
        f"Threshold: {RELEVANCE_THRESHOLD}"
    )

    # low relevance → safer to refuse
    if best_score > RELEVANCE_THRESHOLD:
        logger.warning("Distance exceeds threshold — refusing.")
        return {
            "answer": "REFUSED: No policy found",
            "sources": [],
            "confidence": 0,
            "distance": round(best_score, 3),
            "intent": intent,
            "rewritten": search_query,
            "validation": None,
            "agent_trace": agent_trace
        }

    # build final context from top reranked chunks
    top_docs = docs[:RERANKER_TOP_N]
    top_metas = metas[:RERANKER_TOP_N]

    context = filter_sentences("\n\n".join(top_docs))

    # ---------- LLM answer generation ----------
    answer = extract_answer(context, question)

    # fallback → sometimes LLM refuses even when chunk is strong
    if not answer or answer == "REFUSED: No policy found":
        if best_score < 0.75:
            logger.warning("LLM refused but chunk seems strong — using fallback.")
            return {
                "answer": docs[0][:500],
                "sources": extract_sources([metas[0]]),
                "confidence": round(1 - best_score, 2),
                "distance": round(best_score, 3),
                "intent": intent,
                "rewritten": search_query,
                "validation": None,
                "agent_trace": agent_trace
            }

        return {
            "answer": "REFUSED: No policy found",
            "sources": [],
            "confidence": 0,
            "distance": round(best_score, 3),
            "intent": intent,
            "rewritten": search_query,
            "validation": None,
            "agent_trace": agent_trace
        }

    # ---------- Agent 3 : Answer validation ----------
    # double check whether answer is actually grounded in context
    validation = validate_answer(answer, context, question)

    agent_trace.append({
        "agent": "Answer Validator",
        "input": answer[:100] + "...",
        "output": validation["verdict"],
        "detail": validation["reason"]
    })

    logger.info(f"[Agent 3] Verdict: {validation['verdict']}")

    # hallucination detected → refuse
    if not validation["valid"]:
        logger.warning("Validator flagged hallucination — refusing.")
        return {
            "answer": "REFUSED: Answer could not be verified against source documents.",
            "sources": [],
            "confidence": 0,
            "distance": round(best_score, 3),
            "intent": intent,
            "rewritten": search_query,
            "validation": validation,
            "agent_trace": agent_trace
        }

    # final confidence calculation
    confidence = round(1 - best_score, 2)
    sources = extract_sources(top_metas)

    logger.info(
        f"Final answer ready | Confidence: {confidence} | Sources: {sources}"
    )

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "distance": round(best_score, 3),
        "intent": intent,
        "rewritten": search_query if rewrite_result["changed"] else None,
        "validation": validation,
        "agent_trace": agent_trace
    }