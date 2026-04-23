from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ReportFormat(StrEnum):
    brief_summary = "brief_summary"
    executive_summary = "executive_summary"
    deep_analytical_report = "deep_analytical_report"
    daily_digest = "daily_digest"
    weekly_trend_report = "weekly_trend_report"
    real_time_alert = "real_time_alert"
    industry_snapshot = "industry_snapshot"


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    report_format: ReportFormat = ReportFormat.brief_summary
    region: str | None = Field(default=None, max_length=120)
    industry: str | None = Field(default=None, max_length=120)
    time_window_hours: int = Field(default=72, ge=1, le=24 * 30)


class JobResponse(BaseModel):
    job_id: str
    query: str
    report_format: ReportFormat
    region: str | None = None
    industry: str | None = None
    time_window_hours: int = 72
    status: str
    result: dict[str, Any] | str | None = None
    error: str | None = None
    cached: bool = False
    created_at: datetime
    updated_at: datetime


class FollowupMode(StrEnum):
    follow_up = "follow_up"
    refine_topic = "refine_topic"
    opposing_viewpoints = "opposing_viewpoints"


class FollowupRequest(BaseModel):
    job_id: str
    question: str = Field(min_length=3, max_length=2000)
    mode: FollowupMode = FollowupMode.follow_up


class FollowupResponse(BaseModel):
    job_id: str
    mode: FollowupMode
    answer: str
    refined_query: str | None = None
    suggested_next_questions: list[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    roles: list[str]


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=128)
