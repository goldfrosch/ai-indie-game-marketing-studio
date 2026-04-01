---
name: async-python-patterns
description: Python asyncio 비동기 프로그래밍 패턴 및 베스트 프랙티스
---

# Async Python 패턴

FastAPI 백엔드의 비동기 코드 작성 시 따라야 할 패턴과 주의사항입니다.

## 핵심 원칙

### async def vs def 선택 기준

```python
# ✅ 외부 API 호출, DB I/O → async def
async def fetch_steam_data(app_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}")
        return response.json()

# ✅ CPU 집약 작업, 동기 라이브러리 → def (스레드풀에서 실행)
def process_game_data(raw: dict) -> GameInfo:
    # 무거운 계산, 이미지 처리 등
    ...

# ❌ 동기 I/O를 async def 안에서 호출 금지
async def bad_example():
    import time
    time.sleep(5)  # 이벤트 루프 블로킹!
```

| 상황 | 키워드 | 이유 |
|------|--------|------|
| HTTP 요청, DB 쿼리 | `async def` | I/O 대기 중 이벤트 루프 해제 |
| CPU 연산, 동기 라이브러리 | `def` | FastAPI가 자동으로 스레드풀 실행 |
| 순수 계산 (매우 빠름) | 둘 다 가능 | 오버헤드 무시 가능 |

## HTTP 클라이언트 패턴

### 재사용 가능한 클라이언트

```python
import httpx

# 모듈 수준에서 클라이언트 재사용 (연결 풀링)
class SteamClient:
    def __init__(self, api_key: str):
        self._client: httpx.AsyncClient | None = None
        self._api_key = api_key

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_app_details(self, app_id: int) -> dict:
        client = await self.get_client()
        response = await client.get(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": app_id, "cc": "kr", "l": "korean"}
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.close()
```

- `httpx.AsyncClient`를 매번 생성하지 말고 재사용 (연결 풀 활용)
- FastAPI lifespan에서 close 처리

### 동시 API 호출

```python
import asyncio

async def analyze_multiple_games(app_ids: list[int]) -> list[AnalysisReport]:
    """여러 게임을 동시에 분석"""
    tasks = [analyze_single_game(app_id) for app_id in app_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    reports = []
    for app_id, result in zip(app_ids, results):
        if isinstance(result, Exception):
            logger.error(f"Analysis failed for {app_id}: {result}")
            continue
        reports.append(result)
    return reports
```

- `asyncio.gather()`로 독립 I/O 작업 동시 실행
- `return_exceptions=True`로 일부 실패 시 전체 중단 방지

## 비동기 컨텍스트 매니저

### Lifespan 패턴

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작: 리소스 초기화
    app.state.steam_client = SteamClient(settings.steam_api_key)
    app.state.db_engine = create_async_engine(settings.database_url)
    yield
    # 종료: 리소스 정리
    await app.state.steam_client.close()
    await app.state.db_engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### 비동기 제너레이터 (DB 세션)

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## 백프레셔 & 제한

### 세마포어로 동시성 제한

```python
_semaphore = asyncio.Semaphore(5)  # 최대 5개 동시 요청

async def rate_limited_fetch(url: str) -> dict:
    async with _semaphore:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
```

### 타임아웃

```python
async def fetch_with_timeout(url: str, timeout: float = 10.0) -> dict:
    try:
        async with asyncio.timeout(timeout):
            return await fetch_data(url)
    except TimeoutError:
        raise ExternalAPIError(f"Request to {url} timed out after {timeout}s")
```

## SQLAlchemy 비동기 패턴

### 비동기 세션 사용

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_game_by_steam_id(db: AsyncSession, steam_app_id: int) -> Game | None:
    stmt = select(Game).where(Game.steam_app_id == steam_app_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_game(db: AsyncSession, game_data: GameCreate) -> Game:
    game = Game(**game_data.model_dump())
    db.add(game)
    await db.flush()  # ID 할당을 위해 flush (commit은 get_db에서)
    await db.refresh(game)  # 생성된 필드 반영
    return game
```

### 배치 조회

```python
async def get_games_by_ids(db: AsyncSession, ids: list[int]) -> list[Game]:
    stmt = select(Game).where(Game.id.in_(ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

## 자주 하는 실수

### 1. 이벤트 루프 블로킹

```python
# ❌ 절대 하지 말 것
async def bad():
    import requests
    requests.get("https://api.example.com")  # 동기 HTTP → 루프 블로킹
    time.sleep(5)  # 동기 sleep → 루프 블로킹
    open("file.txt").read()  # 동기 파일 I/O → 루프 블로킹

# ✅ 올바른 방법
async def good():
    async with httpx.AsyncClient() as client:
        await client.get("https://api.example.com")
    await asyncio.sleep(5)
    async with aiofiles.open("file.txt") as f:
        await f.read()
```

### 2. await 누락

```python
# ❌ 코루틴 객체를 반환 (실제 실행 안 됨)
async def get_data():
    return fetch_data()  # await 누락!

# ✅
async def get_data():
    return await fetch_data()
```

### 3. DB 세션 공유

```python
# ❌ 여러 요청이 같은 세션 사용
db_session = None  # 전역 변수

# ✅ 요청마다 새 세션 (Depends로 주입)
async def endpoint(db: AsyncSession = Depends(get_db)):
    ...
```

## FastAPI에서의 비동기 처리 흐름

```
Request → Router (async def) → Service (async def) → DB/External API
                                        ↓
                              asyncio.gather() (병렬 I/O)
                                        ↓
                              Response ← 결과 취합
```

- FastAPI는 `async def` 엔드포인트를 이벤트 루프에서 직접 실행
- `def` 엔드포인트는 스레드풀에서 실행 (블로킹 방지)
- 서비스 계층도 동일한 원칙 적용
