import logging

import faiss
import numpy as np

logger = logging.getLogger(__name__)
DEFAULT_DIMENSION = 384

index = faiss.IndexFlatL2(DEFAULT_DIMENSION)

# Store mapping of vector -> article
metadata_store = []


def _reset_index(dimension: int) -> None:
    global index, metadata_store
    index = faiss.IndexFlatL2(dimension)
    metadata_store = []


def add_embeddings(embeddings, metadata):
    global metadata_store

    if not embeddings or not metadata:
        return

    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim == 1:
        vectors = np.expand_dims(vectors, axis=0)

    if vectors.ndim != 2 or vectors.shape[1] <= 0:
        logger.warning("Skipping invalid embeddings payload for vector store.")
        return

    if vectors.shape[0] != len(metadata):
        valid_count = min(vectors.shape[0], len(metadata))
        vectors = vectors[:valid_count]
        metadata = metadata[:valid_count]

    if vectors.shape[1] != index.d:
        logger.warning(
            "Embedding dimension changed from %s to %s; resetting in-memory vector index.",
            index.d,
            vectors.shape[1],
        )
        _reset_index(vectors.shape[1])

    index.add(vectors)
    metadata_store.extend(metadata)


def search(query_embedding, k=5):
    if index.ntotal == 0 or not metadata_store:
        return []

    query_vector = np.asarray(query_embedding, dtype="float32")
    if query_vector.ndim != 1 or query_vector.shape[0] != index.d:
        return []

    query_vector = np.expand_dims(query_vector, axis=0)
    safe_k = max(1, min(k, len(metadata_store)))
    _, indices = index.search(query_vector, safe_k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(metadata_store):
            results.append(metadata_store[idx])

    return results
