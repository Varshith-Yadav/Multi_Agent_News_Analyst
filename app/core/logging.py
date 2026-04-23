import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def audit_log(event: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    log_path = Path(settings.audit_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        "payload": payload,
    }

    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, default=str))
        file.write("\n")
