import time
import chromadb
from langchain_ollama import OllamaEmbeddings
from src.config import EMBEDDING_MODEL
from src.logger import get_logger

# Logger object used to print structured execution logs
logger = get_logger(__name__)

# Name of the ChromaDB collection where embeddings will be stored
COLLECTION_NAME = "enterprise_rag"

# Number of chunks inserted into DB per batch
# Batch processing improves performance and avoids memory issues
BATCH_SIZE = 100

# Create persistent ChromaDB client → stores vectors locally inside "vector_db" folder
client = chromadb.PersistentClient(path="vector_db")

# Load embedding model from Ollama
# This model converts text chunks into numerical vector embeddings
embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)


def reset_collection():
    """
    Deletes old vector collection if it exists.
    Used when rebuilding index from scratch.
    """
    try:
        client.delete_collection(name=COLLECTION_NAME)
        logger.info("Old collection deleted.")
    except Exception:
        # Happens when collection is not yet created
        logger.info("No previous collection found — creating fresh.")

    # Create new empty collection
    return client.get_or_create_collection(name=COLLECTION_NAME)


def create_embeddings(chunks):

    # Get existing or create new vector collection
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # Extract pure text content from chunk objects
    texts = [chunk.page_content for chunk in chunks]

    # Extract metadata (like source file name, page number)
    metadatas = [chunk.metadata for chunk in chunks]

    # Generate unique ID for each chunk
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    # Logging index build configuration
    logger.info("=" * 60)
    logger.info("INDEX BUILD STARTED")
    logger.info(f"  Total chunks   : {len(texts)}")
    logger.info(f"  Embedding model: {EMBEDDING_MODEL}")
    logger.info(f"  Batch size     : {BATCH_SIZE}")
    logger.info("=" * 60)

    # Start total index build timer
    build_start = time.perf_counter()

    #  STEP 1 : EMBEDDING GENERATION 
    logger.info("STEP 1/2 — Embedding chunks...")
    embed_start = time.perf_counter()

    try:
        # Convert all text chunks into vector embeddings
        embeddings = embedding_model.embed_documents(texts)

        # Calculate embedding execution time
        embed_secs = round(time.perf_counter() - embed_start, 2)

        logger.info(
            f"  Embedding complete in {embed_secs}s "
            f"({round(embed_secs / len(texts), 3)}s per chunk avg)"
        )

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise

    #  STEP 2 : INSERT INTO VECTOR DATABASE 
    logger.info("STEP 2/2 — Inserting into ChromaDB...")
    insert_start = time.perf_counter()

    total_inserted = 0

    # Loop through embeddings in batches for efficient DB insertion
    for start in range(0, len(texts), BATCH_SIZE):

        end = min(start + BATCH_SIZE, len(texts))
        batch_start = time.perf_counter()

        try:
            # Insert batch of vectors into ChromaDB collection
            collection.add(
                documents=texts[start:end],
                metadatas=metadatas[start:end],
                embeddings=embeddings[start:end],
                ids=ids[start:end]
            )

            total_inserted += (end - start)

            # Log batch insertion time
            batch_secs = round(time.perf_counter() - batch_start, 2)
            logger.info(f"  Batch {start+1}–{end} inserted in {batch_secs}s")

        except Exception as e:
            logger.error(f"Failed to insert batch {start}–{end}: {e}")
            raise

    # Calculate final timing metrics
    insert_secs = round(time.perf_counter() - insert_start, 2)
    build_secs  = round(time.perf_counter() - build_start, 2)

    # Final summary log
    logger.info("=" * 60)
    logger.info("INDEX BUILD COMPLETE")
    logger.info(f"  Chunks indexed    : {total_inserted}")
    logger.info(f"  Embedding time    : {embed_secs}s")
    logger.info(f"  Insert time       : {insert_secs}s")
    logger.info(f"  Total build time  : {build_secs}s  ({round(build_secs/60, 1)} min)")
    logger.info("=" * 60)