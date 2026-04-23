from pydantic import BaseModel
from typing import List


class SummaryOutput(BaseModel):
    summary: str


class SentimentOutput(BaseModel):
    sentiment: str  # positive / negative / neutral
    confidence: float


class TrendOutput(BaseModel):
    topics: List[str]


class CredibilityOutput(BaseModel):
    score: float  # 0 to 1
    reasoning: str


class ClaimsOutput(BaseModel):
    claims: List[str]


class VerificationOutput(BaseModel):
    verified: List[str]
    unverified: List[str]


class ConfidenceOutput(BaseModel):
    final_score: float




def build_prompt(task, content):
    return f"""
You are an AI agent.

Task: {task}

Content:
{content}

STRICT RULES:
- Output ONLY valid JSON
- No explanation
- Follow this schema exactly

Return JSON:
"""