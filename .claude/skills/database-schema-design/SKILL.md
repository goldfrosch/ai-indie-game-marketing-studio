---
name: database-schema-design
description: SQLAlchemy ORM 모델 설계 및 데이터베이스 스키마 패턴 가이드
---

# 데이터베이스 스키마 설계

SQLAlchemy ORM 기반 DB 모델 설계 시 따라야 할 가이드입니다.

## 기본 모델 패턴

### Base 클래스 정의

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
```

- `DeclarativeBase`를 상속한 단일 `Base` 클래스 사용
- `TimestampMixin`으로 생성/수정 시간 재사용
- `Mapped[type]` + `mapped_column()` 타입 안전 매핑 사용

### 기본 모델 구조

```python
from sqlalchemy import String, Integer, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Game(TimestampMixin, Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    steam_app_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    developer: Mapped[str | None] = mapped_column(String(200))
    publisher: Mapped[str | None] = mapped_column(String(200))
    price: Mapped[float | None] = mapped_column(Float)
    genres: Mapped[list | None] = mapped_column(JSON)  # ["Action", "RPG"]
    tags: Mapped[list | None] = mapped_column(JSON)     # ["Indie", "Souls-like"]
    description: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[str | None] = mapped_column(String(20))
    review_score: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    header_image: Mapped[str | None] = mapped_column(String(500))
    store_url: Mapped[str | None] = mapped_column(String(500))

    # 관계
    analyses: Mapped[list["AnalysisReport"]] = relationship(back_populates="game", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, name='{self.name}')>"
```

## 필드 타입 매핑

| Python 타입 | SQLAlchemy 타입 | 용도 |
|-------------|----------------|------|
| `int` | `Integer` | 정수 (ID, 수량) |
| `float` | `Float` | 실수 (평점, 가격) |
| `str` | `String(n)` | 짧은 문자열 (이름, URL) |
| `str` | `Text` | 긴 문자열 (설명, 리포트) |
| `bool` | `Boolean` | 플래그 |
| `datetime` | `DateTime` | 시간 |
| `list` / `dict` | `JSON` | 배열/객체 (태그, 장르) |

### 선택적 필드 (nullable)

```python
# 방법 1: Mapped[type | None] (권장)
name: Mapped[str] = mapped_column(nullable=False)        # 필수
developer: Mapped[str | None] = mapped_column()          # 선택 (기본 nullable)

# 방법 2: 명시적 nullable
developer: Mapped[str | None] = mapped_column(String(200), nullable=True)
```

## 관계(Relationship) 설계

### 1:N (일대다)

```python
class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

    analyses: Mapped[list["AnalysisReport"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",  # 게임 삭제시 분석도 삭제
        lazy="selectin",               # 자동 로딩 전략
    )

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    report_type: Mapped[str] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)

    game: Mapped["Game"] = relationship(back_populates="analyses")
```

### M:N (다대다)

```python
from sqlalchemy import Table

# 연결 테이블
game_streamer = Table(
    "game_streamer_matches",
    Base.metadata,
    mapped_column("game_id", ForeignKey("games.id"), primary_key=True),
    mapped_column("streamer_id", ForeignKey("streamers.id"), primary_key=True),
    mapped_column("match_score", Float),
    mapped_column("matched_at", DateTime, default=datetime.utcnow),
)

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    matched_streamers: Mapped[list["Streamer"]] = relationship(secondary=game_streamer, back_populates="matched_games")

class Streamer(Base):
    __tablename__ = "streamers"
    id: Mapped[int] = mapped_column(primary_key=True)
    matched_games: Mapped[list["Game"]] = relationship(secondary=game_streamer, back_populates="matched_streamers")
```

## 인덱스 전략

```python
from sqlalchemy import Index

class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        Index("ix_games_genres", "genres"),          # JSON 필드 인덱스
        Index("ix_games_price_release", "price", "release_date"),  # 복합 인덱스
    )

    # 단일 컬럼 인덱스
    steam_app_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
```

### 인덱스 생성 기준

- **항상 인덱스**: 외래 키(ForeignKey), 유니크 제약조건, 자주 조회하는 필드
- **복합 인덱스**: WHERE + ORDER BY에 자주 함께 사용되는 필드 조합
- **불필요**: 데이터가 적은 테이블, 거의 조회하지 않는 필드

## JSON 필드 사용

```python
class Game(Base):
    # 리스트 저장 (태그, 장르)
    genres: Mapped[list | None] = mapped_column(JSON, default=list)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)

    # 딕셔너리 저장 (메타데이터)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)
```

### JSON 필드 주의사항

- SQLite에서 JSON 쿼리 제한적 → 앱 레벨에서 필터링 고려
- 너무 큰 JSON은 별도 테이블로 정규화 검토
- 기본값으로 `list` / `dict` 함수 참조 사용

## 데이터 무결성

### 제약조건

```python
from sqlalchemy import CheckConstraint, UniqueConstraint

class Game(Base):
    __table_args__ = (
        UniqueConstraint("steam_app_id", name="uq_games_steam_app_id"),
        CheckConstraint("price >= 0", name="ck_games_price_positive"),
    )
```

### Cascade (삭제 전파)

```python
# 부모 삭제시 자식도 삭제
analyses: Mapped[list["AnalysisReport"]] = relationship(
    cascade="all, delete-orphan"
)

# 부모 삭제시 자식의 외래키만 NULL
streamer: Mapped["Streamer | None"] = relationship(
    foreign_keys=[streamer_id],
    ondelete="SET NULL",
)
```

## 쿼리 패턴

### 기본 CRUD

```python
from sqlalchemy import select, update, delete

# Read
async def get_by_id(db: AsyncSession, id: int) -> Game | None:
    result = await db.execute(select(Game).where(Game.id == id))
    return result.scalar_one_or_none()

# Create
async def create(db: AsyncSession, data: GameCreate) -> Game:
    obj = Game(**data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj

# Update
async def update_partial(db: AsyncSession, id: int, data: GameUpdate) -> Game:
    obj = await get_by_id(db, id)
    if obj is None:
        raise NotFoundError(f"Game {id} not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj

# Delete
async def delete_by_id(db: AsyncSession, id: int) -> bool:
    result = await db.execute(delete(Game).where(Game.id == id))
    return result.rowcount > 0
```

### 필터링 & 정렬

```python
async def search_games(
    db: AsyncSession,
    genre: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str = "created_at",
    limit: int = 20,
    offset: int = 0,
) -> list[Game]:
    stmt = select(Game)

    if genre:
        stmt = stmt.where(Game.genres.contains([genre]))  # JSON contains
    if min_price is not None:
        stmt = stmt.where(Game.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Game.price <= max_price)

    stmt = stmt.order_by(getattr(Game, sort_by).desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

## 마이그레이션 (Alembic)

```bash
# 초기 설정
alembic init alembic
alembic revision --autogenerate -m "create games table"

# 마이그레이션 실행
alembic upgrade head

# 롤백
alembic downgrade -1
```

- `Base.metadata.create_all()`은 개발용에만 사용
- 프로덕션은 반드시 Alembic으로 스키마 변경 관리
