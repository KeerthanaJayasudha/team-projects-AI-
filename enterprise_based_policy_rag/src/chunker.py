from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.logger import get_logger

logger = get_logger(__name__)


def chunk_documents(documents):

    logger.info(f"Chunking {len(documents)} pages | chunk_size={CHUNK_SIZE} | overlap={CHUNK_OVERLAP}")

    splitter = RecursiveCharacterTextSplitter( # RecursiveCharacterTextSplitter is used to split large documents into smaller chunk
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )

    # split_documents() converts full document pages into multiple smaller chunks
    # Each chunk will later be converted into embeddings for vector search
    chunks = splitter.split_documents(documents)

    logger.info(f"Chunking complete. Total chunks created: {len(chunks)}")
    return chunks