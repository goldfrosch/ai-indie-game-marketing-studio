---
name: fastapi-python
description: FastAPI 백엔드 개발 베스트 프랙티스 및 아키텍처 가이드
---

# FastAPI Python 백엔드 개발

FastAPI 기반 백엔드 코드를 작성·수정할 때 따라야 할 베스트 프랙티스 가이드입니다.

## 아키텍처 원칙

### 레이어 분리
```
routers/     → HTTP 요청/응답 처리 (입력 검증, 상태 코드)
services/    → 비즈니스 로직 (도메인 규칙, 외부 API 호출)
models/      → SQLAlchemy ORM 모델 (DB 테이블 매핑)
schemas/     → Pydantic 모델 (요청/응답 직렬화, 검증)
db/          → 데이터베이스 설정 및 세션 관리
```

- **Router**: 서비스 계층만 호출. 비즈니스 로직 금지.
- **Service**: 모델/스키마를 조합하여 비즈니스 로직 실행. HTTP 관심사 없음.
- **Model**: DB 테이블 정의. 로직 최소화.
- **Schema**: API 입출력 정의. ORM 모델과 분리.

### 의존성 주입 (Dependency Injection)

```python
from app.dependencies import get_db, get_current_user

@router.post("/games")
async def create_game(
    data: GameCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GameService(db).create(data, user)
```

- `Depends()`를 통해 DB 세션, 인증, 설정 등을 주입
- 서비스 계층은 생성자 주입으로 세션을 받음

## 엔드포인트 설계

### RESTful 규칙

```python
# 리소스는 복수형 명사 사용
GET    /api/games          # 목록
POST   /api/games          # 생성
GET    /api/games/{id}     # 단건 조회
PUT    /api/games/{id}     # 전체 수정
PATCH  /api/games/{id}     # 부분 수정
DELETE /api/games/{id}     # 삭제

# 하위 리소스
GET    /api/games/{id}/analyses     # 게임의 분석 목록
POST   /api/games/{id}/analyses     # 게임 분석 요청
```

### 상태 코드 매핑

```python
from fastapi import status

@router.post("", status_code=status.HTTP_201_CREATED)
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
```

- `200`: 성공 (조회, 수정)
- `201`: 생성됨
- `204`: 삭제됨 (응답 본문 없음)
- `400`: 잘못된 요청 (검증 실패)
- `404`: 리소스 없음
- `422`: Pydantic 검증 실패 (FastAPI 자동 처리)
- `500`: 서버 오류

### 응답 모델 명시

```python
@router.get("/games/{game_id}", response_model=GameResponse)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    ...
```

- `response_model`로 응답 스키마를 명시하면 자동 문서화 + 필드 필터링

## Pydantic 스키마 패턴

### 요청/응답 분리

```python
from pydantic import BaseModel, Field

# 생성 요청
class GameCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    steam_app_id: int | None = None

# 수정 요청 (부분 수정 허용)
class GameUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)

# 응답
class GameResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}  # ORM 모델 → Pydantic 변환 허용
```

### 공통 필드 재사용

```python
class GameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None

class GameCreate(GameBase):
    steam_app_id: int | None = None

class GameUpdate(GameBase):
    name: str | None = None  # 모든 필드 선택적

class GameResponse(GameBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}
```

## 비동기 패턴

### async def 우선

```python
# 외부 API 호출이나 DB 작업이 있으면 항상 async def 사용
@router.get("/games/{game_id}/analyze")
async def analyze_game(game_id: int, db: AsyncSession = Depends(get_db)):
    game = await GameService(db).get(game_id)
    report = await AnalyzerService().analyze(game)
    return report
```

### 백그라운드 작업

```python
from fastapi import BackgroundTasks

@router.post("/games/{game_id}/analyze")
async def request_analysis(
    game_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    background_tasks.add_task(run_analysis, game_id, db)
    return {"status": "processing", "game_id": game_id}
```

## 설정 관리

### pydantic-settings 사용

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    steam_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/gametopia.db"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()  # 모듈 로드 시 한 번만 생성
```

- 환경변수 → `.env` 파일 → 기본값 순서로 해석
- `Settings()` 인스턴스를 전역에서 재사용

## 미들웨어 & CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- 프로덕션에서는 `allow_origins=["*"]` 금지, 실제 도메인 지정

## 테스트 전략

### TestClient 사용

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### 비동기 테스트

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_analyze_game():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/analyze", json={"steam_url": "..."})
    assert response.status_code == 200
```

## 주의사항

- Router에 비즈니스 로직 직접 작성 금지 → Service 계층으로 이동
- 동기 함수(`def`)와 비동기 함수(`async def`) 혼용 시 스레드풀 블로킹 주의
- `Base.metadata.create_all()`은 개발용. 프로덕션은 Alembic 마이그레이션 사용
- 환경변수에 시크릿 하드코딩 금지, `.env` + `.gitignore` 사용
