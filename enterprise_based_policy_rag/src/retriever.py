import time
import chromadb
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import CrossEncoder
from src.config import EMBEDDING_MODEL, RETRIEVAL_K, RERANKER_MODEL, RERANKER_TOP_N
from src.logger import get_logger

logger = get_logger(__name__)

# name of vector collection created during indexing
COLLECTION_NAME = "enterprise_rag"

# persistent chroma client → loads local vector DB from disk
client = chromadb.PersistentClient(path="vector_db")

# embedding model used to convert query text → vector
embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)

# load reranker model once during app startup
# avoids loading model again for every query (performance optimization)
logger.info(f"Loading reranker model: {RERANKER_MODEL}")
reranker = CrossEncoder(RERANKER_MODEL)
logger.info("Reranker ready.")


def retrieve(query):

    # load vector collection
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        logger.error(f"Could not load collection '{COLLECTION_NAME}': {e}")
        raise

    # -------- Stage 1 : Query embedding --------
    # convert user question into embedding vector
    embed_start = time.perf_counter()

    try:
        query_embedding = embedding_model.embed_query(query)
        embed_ms = round((time.perf_counter() - embed_start) * 1000, 1)
    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        raise

    # -------- Stage 2 : Vector similarity search --------
    # fetch top K closest chunks using cosine distance
    search_start = time.perf_counter()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=RETRIEVAL_K,
        include=["documents", "metadatas", "distances"]
    )

    search_ms = round((time.perf_counter() - search_start) * 1000, 1)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    # -------- Stage 3 : Cross-encoder reranking --------
    # vector search is fast but not always very accurate
    # reranker deeply reads query + chunk together and gives better relevance score
    rerank_start = time.perf_counter()

    # create (query, document) pairs
    pairs = [(query, doc) for doc in docs]

    # predict relevance score → higher means more relevant
    rerank_scores = reranker.predict(pairs)

    # combine all info and sort by rerank score (descending)
    ranked = sorted(
        zip(rerank_scores, distances, docs, metas),
        key=lambda x: x[0],
        reverse=True
    )

    rerank_ms = round((time.perf_counter() - rerank_start) * 1000, 1)
    total_ms = round((time.perf_counter() - embed_start) * 1000, 1)

    # -------- Logging detailed retrieval stats --------
    logger.info("=" * 70)
    logger.info(
        f"RETRIEVAL COMPLETE | "
        f"Embed: {embed_ms}ms | "
        f"Search: {search_ms}ms | "
        f"Rerank: {rerank_ms}ms | "
        f"Total: {total_ms}ms"
    )

    # show ranking table in logs (useful during debugging / tuning)
    logger.info(f"{'Rank':<5} {'Status':<12} {'Rerank':>8} {'Dist':>6}  Source")

    for i, (rscore, dist, doc, meta) in enumerate(ranked):
        status = ">>> CHOSEN" if i < RERANKER_TOP_N else "    skipped"
        src = (meta.get("source", "?") if meta else "?").split("/")[-1]
        page = (meta.get("page", 0) or 0) + 1 if meta else "?"
        logger.info(
            f"  {i+1:<4} {status:<12} {round(rscore,4):>8} {round(dist,3):>6}  {src} p.{page}"
        )

    logger.info("=" * 70)

    # return sorted results in same structure expected by rag pipeline
    return {
        "documents": [[r[2] for r in ranked]],
        "metadatas": [[r[3] for r in ranked]],
        "distances": [[r[1] for r in ranked]],
        "rerank_scores": [r[0] for r in ranked],
    }