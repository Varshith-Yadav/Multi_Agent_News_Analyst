import json
import logging
import os
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMCandidate:
    name: str
    model: str
    base_url: str
    api_key: str


XAI_MODEL_DISCOVERY_PRIORITY = (
    "grok-4",
    "grok-4-latest",
    "grok-4.20-reasoning",
    "grok-3-mini",
    "grok-3",
)


def _get_client(candidate: LLMCandidate) -> OpenAI:
    return OpenAI(base_url=candidate.base_url, api_key=candidate.api_key)


def _csv_to_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _is_nvidia_base_url(base_url: str) -> bool:
    return "nvidia.com" in base_url.lower()


def _is_xai_base_url(base_url: str) -> bool:
    normalized = base_url.lower()
    return "api.x.ai" in normalized or ".api.x.ai" in normalized


def _is_local_base_url(base_url: str) -> bool:
    normalized = base_url.lower()
    return any(host in normalized for host in ("localhost", "127.0.0.1", "host.docker.internal"))


def _resolve_api_key(api_key: str | None, api_key_env: str | None) -> str | None:
    if api_key:
        return api_key
    if api_key_env:
        return os.getenv(api_key_env)
    return None


def _parse_fallbacks_json(raw_json: str) -> list[dict[str, Any]]:
    if not raw_json.strip():
        return []
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.warning("Ignoring invalid LLM_FALLBACKS_JSON; expected a JSON array of configs.")
        return []
    if not isinstance(parsed, list):
        logger.warning("Ignoring LLM_FALLBACKS_JSON; value must be a JSON array.")
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _extract_model_id(model: Any) -> str:
    if isinstance(model, dict):
        return str(model.get("id", "")).strip()
    return str(getattr(model, "id", "")).strip()


def _rank_discovered_xai_models(model_ids: list[str]) -> list[str]:
    unique = []
    for model_id in model_ids:
        value = model_id.strip()
        if value and value not in unique:
            unique.append(value)

    ranked: list[str] = []

    for preferred in XAI_MODEL_DISCOVERY_PRIORITY:
        for model_id in unique:
            if model_id == preferred and model_id not in ranked:
                ranked.append(model_id)

    for preferred in XAI_MODEL_DISCOVERY_PRIORITY:
        for model_id in unique:
            if model_id.startswith(f"{preferred}-") and model_id not in ranked:
                ranked.append(model_id)

    for model_id in unique:
        if model_id.startswith("grok-") and model_id not in ranked:
            ranked.append(model_id)

    for model_id in unique:
        if model_id not in ranked:
            ranked.append(model_id)

    return ranked


@lru_cache(maxsize=32)
def _discover_available_models(base_url: str, api_key: str) -> tuple[str, ...]:
    if not api_key or not base_url:
        return ()

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.models.list()
        data = getattr(response, "data", None) or []
    except Exception as exc:
        logger.warning("Model discovery failed for %s: %s", base_url, exc)
        return ()

    discovered = [_extract_model_id(model) for model in data]
    return tuple(_rank_discovered_xai_models(discovered))


def _build_candidates(settings: Settings) -> list[LLMCandidate]:
    candidates: list[LLMCandidate] = []
    seen: set[tuple[str, str]] = set()

    def add_candidate(name: str, model: str, base_url: str, api_key: str | None) -> None:
        if not model or not base_url:
            return
        key = (model, base_url)
        if key in seen:
            return

        if not api_key and not _is_local_base_url(base_url):
            logger.warning(
                "Skipping LLM candidate %s because api key is missing for non-local endpoint %s",
                name,
                base_url,
            )
            return

        effective_key = api_key or "local-dev-key"
        candidates.append(
            LLMCandidate(
                name=name,
                model=model,
                base_url=base_url,
                api_key=effective_key,
            )
        )
        seen.add(key)

    primary_key = (
        _resolve_api_key(settings.llm_api_key, settings.llm_api_key_env)
        or settings.xai_api_key
        or settings.gemini_api_key
        or settings.nvidia_api_key
    )
    if settings.llm_model:
        if _is_nvidia_base_url(settings.llm_base_url) and not primary_key:
            logger.warning(
                "Skipping primary LLM config because NVIDIA endpoint requires an API key."
            )
        else:
            add_candidate(
                name="primary",
                model=settings.llm_model,
                base_url=settings.llm_base_url,
                api_key=primary_key,
            )

    for fallback_model in _csv_to_list(settings.llm_fallback_models_csv):
        add_candidate(
            name=f"fallback:{fallback_model}",
            model=fallback_model,
            base_url=settings.llm_base_url,
            api_key=primary_key,
        )

    for fallback in _parse_fallbacks_json(settings.llm_fallbacks_json):
        model = str(fallback.get("model", "")).strip()
        base_url = str(fallback.get("base_url", "")).strip()
        name = str(fallback.get("name", f"fallback:{model}")).strip() or f"fallback:{model}"
        fallback_api_key = _resolve_api_key(
            str(fallback.get("api_key", "")).strip() or None,
            str(fallback.get("api_key_env", "")).strip() or None,
        )
        add_candidate(
            name=name,
            model=model,
            base_url=base_url,
            api_key=fallback_api_key,
        )

    if settings.gemini_api_key and settings.gemini_model:
        add_candidate(
            name="fallback:gemini",
            model=settings.gemini_model,
            base_url=settings.gemini_base_url,
            api_key=settings.gemini_api_key,
        )

    if primary_key and _is_xai_base_url(settings.llm_base_url):
        discovered_models = list(_discover_available_models(settings.llm_base_url, primary_key))
        for model_id in discovered_models[:6]:
            add_candidate(
                name=f"discovered:{model_id}",
                model=model_id,
                base_url=settings.llm_base_url,
                api_key=primary_key,
            )

    return candidates


def _extract_json_value(content: str) -> Any:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("LLM returned empty content")

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()

    decoder = json.JSONDecoder()

    for index, char in enumerate(cleaned):
        if char not in "[{":
            continue

        try:
            parsed, _ = decoder.raw_decode(cleaned[index:])
            return parsed
        except json.JSONDecodeError:
            continue

    raise ValueError("LLM response did not contain valid JSON")


def _is_non_retryable_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int) and status_code in {400, 401, 403, 404}:
        return True

    message = str(exc).lower()
    if isinstance(status_code, int) and status_code == 429:
        quota_signals = (
            "used all available credits",
            "monthly spending limit",
            "purchase more credits",
            "resource has been exhausted",
            "rate limit",
        )
        if any(signal in message for signal in quota_signals):
            return True

    hard_fail_signals = (
        "model not found",
        "invalid model",
        "unknown model",
        "does not exist",
        "unsupported model",
        "invalid api key",
        "unauthorized",
        "forbidden",
        "permission denied",
    )
    return any(signal in message for signal in hard_fail_signals)


def _local_text_fallback(prompt: str) -> str:
    normalized = re.sub(r"\s+", " ", prompt).strip()
    if not normalized:
        return "No input provided."

    if "json" in normalized.lower():
        return "{}"

    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()]
    if sentences:
        fallback = " ".join(sentences[:3]).strip()
    else:
        fallback = " ".join(normalized.split()[:80]).strip()

    return fallback[:1200] or "No usable content available for fallback."


def call_llm(prompt: str) -> str:
    settings = get_settings()
    candidates = _build_candidates(settings)
    if not candidates:
        if settings.llm_enable_stub_fallback:
            logger.warning("No LLM candidates configured; using local fallback response.")
            return _local_text_fallback(prompt)
        raise RuntimeError(
            "No usable LLM candidate configured. Set LLM_BASE_URL/LLM_MODEL and API key env, "
            "or add entries in LLM_FALLBACKS_JSON."
        )

    last_error: Exception | None = None

    for candidate in candidates:
        client = _get_client(candidate)
        for attempt in range(1, settings.llm_max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=candidate.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful news analysis assistant. "
                                "When the user asks for JSON, respond with valid JSON only and no markdown."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )

                if not response.choices:
                    raise RuntimeError("LLM returned no choices")

                content = response.choices[0].message.content or ""
                if not content.strip():
                    raise RuntimeError("LLM returned empty content")

                return content
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM call failed [%s model=%s] attempt %s/%s: %s",
                    candidate.name,
                    candidate.model,
                    attempt,
                    settings.llm_max_retries,
                    exc,
                )
                if _is_non_retryable_error(exc):
                    break
                if attempt < settings.llm_max_retries:
                    time.sleep(settings.llm_retry_backoff_seconds * attempt)

    if settings.llm_enable_stub_fallback:
        logger.warning("All LLM candidates failed; returning local fallback response.")
        return _local_text_fallback(prompt)

    raise RuntimeError("LLM call failed for all configured providers/models") from last_error


def call_llm_json(prompt: str) -> Any:
    response = call_llm(prompt)
    return _extract_json_value(response)
