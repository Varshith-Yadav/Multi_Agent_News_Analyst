import faiss
import numpy as np

# vector size for MiniLM
DIMENSION = 384

index = faiss.IndexFlatL2(DIMENSION)

# store mapping of vector → article
metadata_store = []


def add_embeddings(embeddings, metadata):
    global metadata_store

    vectors = np.array(embeddings).astype("float32")
    index.add(vectors)

    metadata_store.extend(metadata)


def search(query_embedding, k=5):
    if index.ntotal == 0 or not metadata_store:
        return []

    query_vector = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_vector, k)

    results = []

    for i in indices[0]:
        if 0 <= i < len(metadata_store):
            results.append(metadata_store[i])

    return results
