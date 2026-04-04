import pandas as pd
import faiss
import numpy as np
import os

from services.embedding_service import generate_embedding
from config import DATA_PATH, FAISS_INDEX_PATH, TOP_K

df = pd.read_csv(DATA_PATH)
index = faiss.read_index(FAISS_INDEX_PATH)


def retrieve_similar_tickets(ticket_text):

    query_embedding = generate_embedding(ticket_text)
    query_embedding = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_embedding, TOP_K)

    similar_tickets = []
    similarity_scores = []
    priorities = []
    escalations = []
    categories = []

    for i, idx in enumerate(indices[0]):

        if idx >= len(df):
            continue

        row = df.iloc[idx]

        similarity = float(1 / (1 + distances[0][i]))

        similarity_scores.append(similarity)
        priorities.append(str(row["priority"]))
        categories.append(str(row["category"]))

        escalations.append(
            1 if str(row["escalated"]).lower() in ["1", "true", "yes"] else 0
        )

        similar_tickets.append({
            "title": str(row["title"]),
            "description": str(row["description"]),
            "category": str(row["category"]),
            "priority": str(row["priority"]),
            "resolution": str(row["resolution"])
        })

    return {
        "tickets": similar_tickets,
        "similarity_scores": similarity_scores,
        "priorities": priorities,
        "escalations": escalations,
        "categories": categories
    }