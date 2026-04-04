import pandas as pd
import faiss
import numpy as np

from services.embedding_service import generate_embedding

df = pd.read_csv("data/historical_tickets.csv")

embeddings = np.array([
    generate_embedding(row["title"] + " " + row["description"])
    for _, row in df.iterrows()
]).astype("float32")

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

faiss.write_index(index, "embeddings/faiss_index.bin")

print("FAISS index created successfully")