import re

from app.core.config import get_settings


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _clip_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).strip() + "..."


def remove_long_quotes(text: str, max_quote_words: int) -> str:
    def _replace(match: re.Match[str]) -> str:
        quote = match.group(0)
        words = quote.strip("\"' ").split()
        if len(words) <= max_quote_words:
            return quote
        truncated = " ".join(words[:max_quote_words]).strip()
        return f"\"{truncated} ...\""

    text = re.sub(r'"[^"]+"', _replace, text)
    text = re.sub(r"'[^']+'", _replace, text)
    return text


def copyright_safe_text(text: str, max_words: int | None = None) -> str:
    settings = get_settings()
    if not settings.enforce_copyright_controls:
        return text.strip()

    effective_max_words = max_words or settings.max_summary_words
    normalized = _normalize_whitespace(text)
    dequoted = remove_long_quotes(normalized, settings.max_quote_words)
    return _clip_words(dequoted, effective_max_words)


def safe_evidence_snippet(text: str, max_words: int = 18) -> str:
    cleaned = _normalize_whitespace(text)
    return _clip_words(cleaned, max_words)
