from sentence_transformers import SentenceTransformer

from backend.utils.config import EMBED_MODEL


class Embedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBED_MODEL
        self.model = SentenceTransformer(self.model_name)

    def embed_documents(self, texts):
        if not texts:
            return []

        cleaned = [t.strip() for t in texts if t and t.strip()]

        if not cleaned:
            return []

        embeddings = self.model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embeddings.tolist()

    def embed_query(self, query: str):
        if not query or not query.strip():
            return []

        embedding = self.model.encode(
            query.strip(),
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embedding.tolist()