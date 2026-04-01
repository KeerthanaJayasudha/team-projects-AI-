import re
from typing import List, Dict, Any, Optional

import ollama

from backend.utils.logger import get_logger
from backend.utils.config import LLM_MODEL, OLLAMA_HOST

logger = get_logger(__name__)


class RAGPipeline:
    def __init__(self, vectordb=None, embedder=None, model_name: Optional[str] = None):
        self.vectordb = vectordb
        self.embedder = embedder
        self.model_name = model_name or LLM_MODEL
        self.ollama_host = OLLAMA_HOST
        self.client = ollama.Client(host=self.ollama_host)

    def _embed_query(self, question: str):
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if self.embedder is None:
            raise ValueError("Embedder is not initialized")

        if hasattr(self.embedder, "embed_query"):
            return self.embedder.embed_query(question)

        raise AttributeError("Embedding model has no valid encode method.")

    def _normalize_text(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _tokenize(self, text: str) -> set:
        normalized = self._normalize_text(text)
        return set(normalized.split()) if normalized else set()

    def _heading_overlap_score(self, question: str, section: str, title: str) -> float:
        q_words = self._tokenize(question)
        s_words = self._tokenize(section)
        t_words = self._tokenize(title)

        if not q_words:
            return 0.0

        section_overlap = len(q_words & s_words) / max(len(q_words), 1)
        title_overlap = len(q_words & t_words) / max(len(q_words), 1)

        return (section_overlap * 0.22) + (title_overlap * 0.18)

    def _content_overlap_score(self, question: str, content: str) -> float:
        q_words = self._tokenize(question)
        c_words = self._tokenize(content)

        if not q_words or not c_words:
            return 0.0

        overlap = len(q_words & c_words) / max(len(q_words), 1)
        return overlap * 0.20

    def _distance_to_similarity(self, dist: Any) -> float:
        try:
            value = float(dist)
            similarity = 1.0 - value
            return max(0.0, min(1.0, similarity))
        except Exception:
            return 0.0

    def _score_chunk(
        self,
        question: str,
        content: str,
        section: str,
        title: str,
        dist: Any
    ) -> Dict[str, float]:
        base_similarity = self._distance_to_similarity(dist)
        heading_bonus = self._heading_overlap_score(question, section, title)
        content_bonus = self._content_overlap_score(question, content)

        final_score = round(base_similarity + heading_bonus + content_bonus, 4)

        return {
            "base_similarity": round(base_similarity, 4),
            "heading_bonus": round(heading_bonus, 4),
            "content_bonus": round(content_bonus, 4),
            "final_score": final_score
        }

    def _clean_model_output(self, text: str) -> str:
        if not text:
            return "I could not find this information in the crawled sources."

        cleaned = text.strip()

        # Remove common meta-commentary
        unwanted_patterns = [
            r"(?i)^according to source \d+[:,]?\s*",
            r"(?i)^according to the provided context[:,]?\s*",
            r"(?i)^according to the context[:,]?\s*",
            r"(?i)^based on the provided context[:,]?\s*",
            r"(?i)^based on the context[:,]?\s*",
            r"(?i)^this answer does not align with the provided context\.?\s*",
            r"(?i)^this aligns with the context provided.*?\.?\s*",
            r"(?i)^from source \d+[:,]?\s*",
        ]

        for pattern in unwanted_patterns:
            cleaned = re.sub(pattern, "", cleaned).strip()

        stop_markers = [
            "\nContext:",
            "\nQuestion:",
            "\nFinal Answer:",
            "\nRules:",
            "Source 1",
            "Source 2",
            "Source 3",
            "Source 4",
        ]

        for marker in stop_markers:
            idx = cleaned.find(marker)
            if idx != -1:
                cleaned = cleaned[:idx].strip()

        cleaned = re.sub(r"\n{2,}", "\n\n", cleaned).strip()

        if not cleaned:
            cleaned = "I could not find this information in the crawled sources."

        return cleaned

    def _deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []

        for chunk in chunks:
            key = (
                chunk.get("url", ""),
                chunk.get("section", ""),
                chunk.get("content", "")[:200]
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(chunk)

        return unique

    def _build_context(self, chunks: List[Dict[str, Any]], max_chunks: int) -> str:
        selected = chunks[:max_chunks]
        context_parts = []

        for i, chunk in enumerate(selected, 1):
            block = (
                f"[Document {i}]\n"
                f"Title: {chunk['title']}\n"
                f"Section: {chunk['section']}\n"
                f"URL: {chunk['url']}\n"
                f"Text: {chunk['content']}"
            )
            context_parts.append(block)

        return "\n\n".join(context_parts)

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        confidence_threshold: float = 0.20,
        where: Optional[dict] = None
    ) -> List[Dict[str, Any]]:
        try:
            if self.vectordb is None:
                logger.warning("VectorDB is not initialized")
                return []

            query_embedding = self._embed_query(question)
            initial_fetch_k = max(top_k * 4, 8)

            results = self.vectordb.query(
                query_embedding=query_embedding,
                top_k=initial_fetch_k,
                where=where
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            retrieved = []

            for doc, meta, dist, chunk_id in zip(documents, metadatas, distances, ids):
                if not doc or not meta:
                    continue

                title = meta.get("title", "Untitled")
                section = meta.get("section", "General")
                url = meta.get("url", "")

                score_parts = self._score_chunk(
                    question=question,
                    content=doc,
                    section=section,
                    title=title,
                    dist=dist
                )

                if score_parts["final_score"] < confidence_threshold:
                    continue

                retrieved.append({
                    "content": doc,
                    "url": url,
                    "title": title,
                    "section": section,
                    "chunk_id": chunk_id,
                    "confidence": score_parts["final_score"],
                    "base_similarity": score_parts["base_similarity"],
                    "heading_bonus": score_parts["heading_bonus"],
                    "content_bonus": score_parts["content_bonus"],
                    "crawl_id": meta.get("crawl_id")
                })

            retrieved.sort(key=lambda x: x["confidence"], reverse=True)
            retrieved = self._deduplicate_chunks(retrieved)

            return retrieved[:top_k]

        except Exception as e:
            logger.exception(f"Retrieval Error: {e}")
            return []

    def answer(
        self,
        question: str,
        top_k: int = 5,
        where: Optional[dict] = None
    ) -> Dict[str, Any]:
        try:
            retrieved_chunks = self.retrieve(
                question=question,
                top_k=top_k,
                where=where
            )

            if not retrieved_chunks:
                return {
                    "answer": "I could not find this information in the crawled sources.",
                    "sources": []
                }

            strongest_score = retrieved_chunks[0]["confidence"] if retrieved_chunks else 0.0
            if strongest_score < 0.25:
                return {
                    "answer": "I could not find this information in the crawled sources.",
                    "sources": []
                }

            # Use fewer but better chunks
            max_context_chunks = min(max(top_k, 2), 4)
            context = self._build_context(retrieved_chunks, max_context_chunks)

            prompt = f"""
You are a question-answering assistant.

Answer the user's question ONLY using the retrieved text below.

Strict rules:
- Give a direct answer only.
- Do NOT say phrases like "according to the source", "according to the context", "this aligns with", or "based on the provided context".
- Do NOT mention document numbers.
- Do NOT explain your reasoning.
- Do NOT add extra commentary.
- If the answer is a definition, give the exact definition in simple form.
- If the answer is not clearly present, say exactly:
I could not find this information in the crawled sources.

Retrieved text:
{context}

User question:
{question}

Answer:
"""

            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.0
                }
            )

            raw_answer = response["message"]["content"].strip()
            final_answer = self._clean_model_output(raw_answer)

            seen = set()
            unique_sources = []

            for chunk in retrieved_chunks[:max_context_chunks]:
                key = (chunk["url"], chunk["section"])
                if key in seen:
                    continue

                seen.add(key)
                unique_sources.append({
                    "url": chunk["url"],
                    "title": chunk["title"],
                    "section": chunk["section"],
                    "confidence": chunk["confidence"],
                    "crawl_id": chunk.get("crawl_id")
                })

            return {
                "answer": final_answer,
                "sources": unique_sources
            }

        except Exception as e:
            logger.exception(f"Generation Error: {e}")
            return {
                "answer": "An internal error occurred while generating the answer.",
                "sources": []
            }