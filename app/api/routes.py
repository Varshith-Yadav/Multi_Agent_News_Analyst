from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.cache import get_cached_analysis
from app.core.config import get_settings
from app.core.job_store import JobRecord, create_job, enqueue_job, get_job
from app.core.logging import audit_log
from app.core.security import TokenData, authenticate_user, create_access_token, register_user
from app.deps import require_roles
from app.schemas.query import (
    FollowupRequest,
    FollowupResponse,
    QueryRequest,
    SignupRequest,
    TokenResponse,
)
from app.services.conversation_service import generate_followup_response

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    auth = authenticate_user(form_data.username, form_data.password)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, roles = auth
    token = create_access_token(username, roles)
    settings = get_settings()
    return TokenResponse(
        access_token=token,
        expires_in=settings.auth_token_expire_minutes * 60,
        roles=roles,
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest) -> TokenResponse:
    try:
        username, roles = register_user(req.username, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = create_access_token(username, roles)
    settings = get_settings()
    audit_log("signup_completed", {"user": username, "roles": roles})
    return TokenResponse(
        access_token=token,
        expires_in=settings.auth_token_expire_minutes * 60,
        roles=roles,
    )


@router.post("/analyze", response_model=JobRecord, status_code=status.HTTP_202_ACCEPTED)
async def analyze_news(
    req: QueryRequest,
    user: TokenData = Depends(require_roles("analyst", "admin")),
) -> JobRecord:
    request_payload = {
        "query": req.query,
        "report_format": req.report_format.value,
        "region": req.region,
        "industry": req.industry,
        "time_window_hours": req.time_window_hours,
    }
    cached_result = await get_cached_analysis(request_payload)
    job = await create_job(
        req.query,
        report_format=req.report_format,
        region=req.region,
        industry=req.industry,
        time_window_hours=req.time_window_hours,
        cached_result=cached_result,
    )

    if not job.cached:
        await enqueue_job(job)

    audit_log(
        "analyze_requested",
        {
            "job_id": job.job_id,
            "user": user.sub,
            "query": req.query,
            "report_format": req.report_format.value,
            "region": req.region,
            "industry": req.industry,
            "time_window_hours": req.time_window_hours,
            "cached": job.cached,
        },
    )

    return job


@router.get("/result/{job_id}", response_model=JobRecord)
async def get_result(
    job_id: str,
    user: TokenData = Depends(require_roles("viewer", "analyst", "admin")),
) -> JobRecord:
    job = await get_job(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid job_id")

    audit_log("result_retrieved", {"job_id": job_id, "user": user.sub, "status": job.status})
    return job


@router.post("/follow-up", response_model=FollowupResponse)
async def follow_up(
    req: FollowupRequest,
    user: TokenData = Depends(require_roles("viewer", "analyst", "admin")),
) -> FollowupResponse:
    job = await get_job(req.job_id)
    if job is None or job.result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed report found for this job_id.",
        )
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is not completed yet. Try again after analysis finishes.",
        )

    report = job.result if isinstance(job.result, dict) else {"summary": str(job.result)}
    followup = generate_followup_response(mode=req.mode, question=req.question, report=report)

    audit_log(
        "followup_queried",
        {
            "job_id": req.job_id,
            "user": user.sub,
            "mode": req.mode.value,
            "question": req.question,
        },
    )

    return FollowupResponse(
        job_id=req.job_id,
        mode=req.mode,
        answer=followup["answer"],
        refined_query=followup.get("refined_query"),
        suggested_next_questions=followup.get("suggested_next_questions", []),
    )
