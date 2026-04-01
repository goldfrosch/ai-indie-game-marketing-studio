from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    steam_app_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    developer: Mapped[str | None] = mapped_column(String(500))
    publisher: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[float | None] = mapped_column(Float)
    genres: Mapped[str | None] = mapped_column(Text)  # JSON string
    tags: Mapped[str | None] = mapped_column(Text)  # JSON string
    description: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[str | None] = mapped_column(String(20))
    review_score: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    header_image: Mapped[str | None] = mapped_column(String(1000))
    store_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now())


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(Integer, index=True)
    report_type: Mapped[str] = mapped_column(String(50))  # full, quick, tag_optimization
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[str | None] = mapped_column(Text)  # JSON string
    weaknesses: Mapped[str | None] = mapped_column(Text)  # JSON string
    recommendations: Mapped[str | None] = mapped_column(Text)  # JSON string
    full_report: Mapped[str | None] = mapped_column(Text)  # Full AI response
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
