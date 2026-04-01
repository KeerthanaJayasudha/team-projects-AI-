from typing import Dict, List, Any


def precision_at_k_auto(
    retrieved_chunks: List[Dict[str, Any]],
    k: int = 3,
    threshold: float = 0.30
) -> float:
    if k <= 0:
        return 0.0

    retrieved_k = retrieved_chunks[:k]
    if not retrieved_k:
        return 0.0

    hits = sum(
        1 for chunk in retrieved_k
        if float(chunk.get("confidence", 0.0)) >= threshold
    )
    return hits / k


def recall_at_k_auto(
    retrieved_chunks: List[Dict[str, Any]],
    k: int = 3,
    threshold: float = 0.30
) -> float:
    if k <= 0 or not retrieved_chunks:
        return 0.0

    total_relevant = sum(
        1 for chunk in retrieved_chunks
        if float(chunk.get("confidence", 0.0)) >= threshold
    )

    if total_relevant == 0:
        return 0.0

    retrieved_k = retrieved_chunks[:k]
    hits = sum(
        1 for chunk in retrieved_k
        if float(chunk.get("confidence", 0.0)) >= threshold
    )

    return hits / total_relevant


def evaluate_query(
    retrieved_chunks: List[Dict[str, Any]],
    k: int = 3,
    threshold: float = 0.30
) -> Dict[str, float]:
    precision = precision_at_k_auto(
        retrieved_chunks=retrieved_chunks,
        k=k,
        threshold=threshold
    )
    recall = recall_at_k_auto(
        retrieved_chunks=retrieved_chunks,
        k=k,
        threshold=threshold
    )

    return {
        "precision@k": round(precision, 3),
        "recall@k": round(recall, 3)
    }