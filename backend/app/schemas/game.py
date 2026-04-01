from datetime import datetime

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Steam store URL or app ID")


class GameInfo(BaseModel):
    steam_app_id: int | None = None
    name: str
    developer: str | None = None
    publisher: str | None = None
    price: float | None = None
    genres: list[str] = []
    tags: list[str] = []
    description: str | None = None
    release_date: str | None = None
    review_score: float | None = None
    review_count: int | None = None
    header_image: str | None = None
    store_url: str | None = None


class AnalysisResponse(BaseModel):
    id: int
    game: GameInfo
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    created_at: datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
