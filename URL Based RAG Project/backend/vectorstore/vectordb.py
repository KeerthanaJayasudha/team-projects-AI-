import chromadb

from backend.utils.config import CHROMA_PATH
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VectorDB:
    def __init__(self, collection_name="url_rag_collection", persist_dir=CHROMA_PATH):
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)

            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(
                f"VectorDB initialized | collection={collection_name} | path={persist_dir}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize VectorDB: {e}")
            raise

    def add_documents(self, documents, embeddings, metadatas, ids):
        if not documents:
            logger.warning("No documents to add to vector database")
            return

        if not (len(documents) == len(embeddings) == len(metadatas) == len(ids)):
            raise ValueError("documents, embeddings, metadatas, and ids must have same length")

        try:
            self.collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Stored {len(documents)} chunks in vector database")

        except Exception as e:
            logger.error(f"Failed to store documents in vector database: {e}")
            raise

    def delete_by_url(self, url):
        try:
            results = self.collection.get(include=["metadatas"])

            ids_to_delete = []

            for meta, doc_id in zip(
                results.get("metadatas", []),
                results.get("ids", [])
            ):
                if meta and meta.get("url") == url:
                    ids_to_delete.append(doc_id)

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} chunks belonging to URL: {url}")
            else:
                logger.info(f"No chunks found for URL: {url}")

        except Exception as e:
            logger.error(f"Failed to delete chunks for URL '{url}': {e}")
            raise

    def delete_by_url_section(self, url, section):
        try:
            results = self.collection.get(include=["metadatas"])

            ids_to_delete = []

            for meta, doc_id in zip(
                results.get("metadatas", []),
                results.get("ids", [])
            ):
                if meta and meta.get("url") == url and meta.get("section") == section:
                    ids_to_delete.append(doc_id)

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)

                logger.info(
                    f"Deleted {len(ids_to_delete)} chunks for URL='{url}', section='{section}'"
                )
            else:
                logger.info(f"No chunks found for URL='{url}', section='{section}'")

        except Exception as e:
            logger.error(f"Failed to delete chunks for URL='{url}', section='{section}': {e}")
            raise

    def query(self, query_embedding, top_k=5, where=None):
        """
        Perform similarity search.

        We intentionally fetch more candidates than top_k
        so the RAG pipeline can re-rank results.
        """

        try:
            fetch_k = max(top_k * 4, 10)

            logger.info(
                f"Running similarity search | requested={top_k} | fetch={fetch_k} | where={where}"
            )

            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": fetch_k,
                "include": ["documents", "metadatas", "distances"]
            }

            if where:
                query_kwargs["where"] = where

            results = self.collection.query(**query_kwargs)

            return results

        except Exception as e:
            logger.error(f"Vector database query failed: {e}")
            raise

    def count(self):
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to count vector database documents: {e}")
            raise

    def clear(self):
        try:
            results = self.collection.get()
            ids = results.get("ids", [])

            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents from vector database")
            else:
                logger.info("Vector database already empty")

        except Exception as e:
            logger.error(f"Failed to clear vector database: {e}")
            raise

    def get_chunk_samples(self, limit=20, where=None):
        """
        Debug helper for inspecting stored chunks.
        """

        try:
            kwargs = {
                "include": ["metadatas", "documents"]
            }

            if where:
                kwargs["where"] = where

            results = self.collection.get(**kwargs)

            ids = results.get("ids", [])[:limit]
            metadatas = results.get("metadatas", [])[:limit]
            documents = results.get("documents", [])[:limit]

            rows = []

            for i, chunk_id in enumerate(ids):
                rows.append({
                    "chunk_id": chunk_id,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "document_preview": (
                        documents[i][:200]
                        if i < len(documents) and documents[i]
                        else ""
                    )
                })

            return rows

        except Exception as e:
            logger.error(f"Failed to fetch chunk samples: {e}")
            raise