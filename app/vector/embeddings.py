from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

settings = get_settings()
model = SentenceTransformer(settings.embedding_model)


def get_embedding(text: str):
    return model.encode(text)
