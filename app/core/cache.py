import hashlib
import json
from typing import Any

from app.core.config import get_settings
from app.core.redis import get_redis
from app.core.security import decrypt_json, encrypt_json


def _cache_key(request_payload: dict[str, Any]) -> str:
    normalized = json.dumps(request_payload, sort_keys=True, ensure_ascii=False, default=str)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    settings = get_settings()
    return f"{settings.cache_key_prefix}:{digest}"


async def get_cached_analysis(request_payload: dict[str, Any]) -> dict[str, Any] | None:
    redis = await get_redis()
    payload = await redis.get(_cache_key(request_payload))

    if not payload:
        return None

    return decrypt_json(payload)


async def set_cached_analysis(request_payload: dict[str, Any], result: dict[str, Any]) -> None:
    settings = get_settings()
    redis = await get_redis()
    payload = encrypt_json(result)
    await redis.set(
        _cache_key(request_payload),
        payload,
        ex=settings.cache_ttl_seconds,
    )
