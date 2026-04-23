import asyncio
import logging

from app.core.cache import set_cached_analysis
from app.core.config import get_settings
from app.core.graph_builder import build_graph
from app.core.logging import audit_log, configure_logging
from app.core.job_store import JobStatus, pop_job, update_job
from app.db.init_db import init_db

logger = logging.getLogger(__name__)
configure_logging()
graph = build_graph()


async def run_job(job_id: str, request_payload: dict[str, str | int | None]) -> None:
    try:
        await update_job(job_id, status=JobStatus.running, error=None)

        state = request_payload
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, graph.invoke, state)

        report = result.get("report") or result
        await update_job(job_id, status=JobStatus.completed, result=report, error=None)
        await set_cached_analysis(request_payload, report)
        audit_log(
            "job_completed",
            {
                "job_id": job_id,
                "query": request_payload.get("query"),
                "report_format": request_payload.get("report_format"),
                "confidence": report.get("confidence"),
            },
        )
        logger.info("Job completed", extra={"job_id": job_id})
    except Exception as exc:
        logger.exception("Job failed", extra={"job_id": job_id})
        await update_job(job_id, status=JobStatus.failed, error=str(exc), result=None)
        audit_log(
            "job_failed",
            {"job_id": job_id, "query": request_payload.get("query"), "error": str(exc)},
        )


async def run_worker() -> None:
    settings = get_settings()
    init_db()
    logger.info("Worker started", extra={"queue": settings.job_queue_key})

    while True:
        job = await pop_job(timeout_seconds=settings.worker_poll_timeout_seconds)
        if job is None:
            continue

        payload = {
            "query": job.query,
            "report_format": job.report_format,
            "region": job.region,
            "industry": job.industry,
            "time_window_hours": job.time_window_hours,
        }
        await run_job(job.job_id, payload)


if __name__ == "__main__":
    asyncio.run(run_worker())
