# import json
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer


# class VectorStore:

#     def __init__(self, json_file):

#         # Load embedding model
#         self.model = SentenceTransformer("all-MiniLM-L6-v2")

#         # Load documents
#         with open(json_file, "r") as f:
#             self.docs = json.load(f)

#         # Extract text
#         self.texts = [doc["text"] for doc in self.docs]

#         # Generate embeddings
#         embeddings = self.model.encode(self.texts)

#         dimension = embeddings.shape[1]

#         # Create FAISS index
        
#         self.index = faiss.IndexFlatIP(dimension)

#         faiss.normalize_L2(embeddings)

#         self.index.add(np.array(embeddings).astype("float32"))

#         # Add embeddings to index
#         self.index.add(np.array(embeddings).astype("float32"))

#     def search(self, query, k=3):

#         # Encode query
#         query_embedding = self.model.encode([query]).astype("float32")

#         # Search similar vectors
        
#         query_embedding = self.model.encode([query]).astype("float32")

#         faiss.normalize_L2(query_embedding)

#         results = []

#         for idx in indices[0]:
#             results.append(self.docs[idx])

#         return results
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:

    def __init__(self, json_file):

        # Load embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # Load documents
        with open(json_file, "r") as f:
            self.docs = json.load(f)

        # Extract text
        self.texts = [doc["text"] for doc in self.docs]

        # Generate embeddings
        embeddings = self.model.encode(self.texts)

        embeddings = np.array(embeddings).astype("float32")

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]

        # Create FAISS index using cosine similarity
        self.index = faiss.IndexFlatIP(dimension)

        # Add embeddings
        self.index.add(embeddings)

    def search(self, query, k=3):

        # Encode query
        query_embedding = self.model.encode([query]).astype("float32")

        # Normalize query vector
        faiss.normalize_L2(query_embedding)

        # Search
        distances, indices = self.index.search(query_embedding, k)

        results = []

        for idx in indices[0]:
            results.append(self.docs[idx])

        return results