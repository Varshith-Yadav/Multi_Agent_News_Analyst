from app.vector.embeddings import get_embedding
from app.vector.store import search


def semantic_search(query: str, k: int = 5):
    query_embedding = get_embedding(query)
    return search(query_embedding, k)
