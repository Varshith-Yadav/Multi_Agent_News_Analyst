import hashlib
import logging
import math
import re
from functools import lru_cache
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - import fallback for minimal runtime envs
    SentenceTransformer = None  # type: ignore[assignment]

from app.core.config import get_settings

logger = logging.getLogger(__name__)
FALLBACK_DIMENSION = 384


@lru_cache(maxsize=1)
def _load_model() -> Any | None:
    if SentenceTransformer is None:
        logger.warning("sentence-transformers not installed; using hash fallback embeddings.")
        return None

    settings = get_settings()
    try:
        return SentenceTransformer(settings.embedding_model)
    except Exception as exc:
        logger.warning("Embedding model load failed; using hash fallback embeddings: %s", exc)
        return None


def _hash_embedding(text: str, dimension: int = FALLBACK_DIMENSION) -> list[float]:
    tokens = re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
    if not tokens:
        return [0.0] * dimension

    vector = [0.0] * dimension
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def get_embedding(text: str):
    model = _load_model()
    if model is None:
        return _hash_embedding(text)

    try:
        return model.encode(text or "")
    except Exception as exc:
        logger.warning("Embedding inference failed; using hash fallback embedding: %s", exc)
        return _hash_embedding(text)
