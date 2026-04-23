import json
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.redis import get_redis
from app.core.security import decrypt_json, encrypt_json
from app.schemas.query import ReportFormat

_UNSET = object()


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobRecord(BaseModel):
    job_id: str
    query: str
    report_format: ReportFormat = ReportFormat.brief_summary
    region: str | None = None
    industry: str | None = None
    time_window_hours: int = 72
    status: JobStatus
    result: dict[str, Any] | str | None = None
    error: str | None = None
    cached: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QueuePayload(BaseModel):
    job_id: str
    query: str
    report_format: ReportFormat = ReportFormat.brief_summary
    region: str | None = None
    industry: str | None = None
    time_window_hours: int = 72


def _job_key(job_id: str) -> str:
    settings = get_settings()
    return f"{settings.job_key_prefix}:{job_id}"


async def _save_job(job: JobRecord) -> JobRecord:
    settings = get_settings()
    redis = await get_redis()
    payload = encrypt_json(job.model_dump(mode="json"))
    await redis.set(
        _job_key(job.job_id),
        payload,
        ex=settings.job_ttl_seconds,
    )
    return job


async def create_job(
    query: str,
    *,
    report_format: ReportFormat = ReportFormat.brief_summary,
    region: str | None = None,
    industry: str | None = None,
    time_window_hours: int = 72,
    cached_result: dict[str, Any] | None = None,
) -> JobRecord:
    status = JobStatus.completed if cached_result else JobStatus.queued
    now = datetime.now(UTC)
    job = JobRecord(
        job_id=str(uuid.uuid4()),
        query=query,
        report_format=report_format,
        region=region,
        industry=industry,
        time_window_hours=time_window_hours,
        status=status,
        result=cached_result,
        cached=bool(cached_result),
        created_at=now,
        updated_at=now,
    )
    return await _save_job(job)


async def enqueue_job(job: JobRecord) -> None:
    settings = get_settings()
    redis = await get_redis()
    payload = QueuePayload(
        job_id=job.job_id,
        query=job.query,
        report_format=job.report_format,
        region=job.region,
        industry=job.industry,
        time_window_hours=job.time_window_hours,
    )
    await redis.rpush(
        settings.job_queue_key,
        json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
    )


async def update_job(
    job_id: str,
    *,
    status: JobStatus | None = None,
    result: dict[str, Any] | str | None | object = _UNSET,
    error: str | None = None,
) -> JobRecord | None:
    current = await get_job(job_id)
    if current is None:
        return None

    updated = current.model_copy(
        update={
            "status": status or current.status,
            "result": current.result if result is _UNSET else result,
            "error": error,
            "updated_at": datetime.now(UTC),
        }
    )
    return await _save_job(updated)


async def get_job(job_id: str) -> JobRecord | None:
    redis = await get_redis()
    payload = await redis.get(_job_key(job_id))
    if not payload:
        return None
    parsed = decrypt_json(payload)
    return JobRecord.model_validate(parsed)


async def pop_job(*, timeout_seconds: int | None = None) -> QueuePayload | None:
    settings = get_settings()
    redis = await get_redis()
    timeout = timeout_seconds
    if timeout is None:
        timeout = settings.worker_poll_timeout_seconds

    payload = await redis.blpop(settings.job_queue_key, timeout=timeout)
    if not payload:
        return None

    _, raw_message = payload
    return QueuePayload.model_validate(json.loads(raw_message))
