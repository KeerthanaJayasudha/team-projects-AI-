from src.loader import load_documents
from src.chunker import chunk_documents
from src.embedder import create_embeddings, reset_collection
from src.rag import rag_answer
from src.logger import get_logger

logger = get_logger(__name__)


def build_index():

    logger.info("=" * 50)
    logger.info("BUILD MODE STARTED")
    logger.info("=" * 50)

    documents = load_documents()
    logger.info(f"Total pages loaded: {len(documents)}")

    chunks = chunk_documents(documents)
    logger.info(f"Total chunks created: {len(chunks)}")

    reset_collection()

    create_embeddings(chunks)

    logger.info("Index build complete.")
    print("\nIndex built successfully.")


def chat():

    logger.info("=" * 50)
    logger.info("CHAT MODE STARTED")
    logger.info("=" * 50)

    print("\nRAG system ready. Type 'exit' to quit.\n")

    while True:

        question = input("Ask Question (or type exit): ").strip()

        if not question:
            continue

        if question.lower() == "exit":
            logger.info("Chat session ended by user.")
            break

        print("\nSearching...")

        result = rag_answer(question)

        print("\n" + "=" * 50)
        print("ANSWER:\n")
        print(result["answer"])

        if result["sources"]:
            print("\nSOURCES:")
            for s in result["sources"]:
                print(f"  - {s}")

        print(f"\nDistance : {result['distance']}")
        print(f"Confidence: {result['confidence']}")
        print("=" * 50 + "\n")


if __name__ == "__main__":

    mode = input("Type 'build' to rebuild index or 'chat' to query: ").strip().lower()

    if mode == "build":
        build_index()
    elif mode == "chat":
        chat()
    else:
        logger.warning(f"Unknown mode entered: '{mode}'")
        print(f"Unknown mode: '{mode}'. Please type 'build' or 'chat'.")