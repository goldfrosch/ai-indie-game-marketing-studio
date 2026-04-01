---
name: python-error-handling
description: FastAPI 백엔드 에러 핸들링 및 예외 처리 패턴
---

# Python 에러 핸들링

FastAPI 백엔드에서 일관되고 안전한 에러 처리를 위한 가이드입니다.

## 커스텀 예외 계층

### 기본 구조

```python
class AppError(Exception):
    """애플리케이션 기본 예외"""
    def __init__(self, message: str, status_code: int = 500, detail: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            message=f"{resource}을(를) 찾을 수 없습니다",
            status_code=404,
            detail={"resource": resource, "id": str(resource_id)},
        )

class ExternalAPIError(AppError):
    def __init__(self, service: str, message: str, status_code: int = 502):
        super().__init__(
            message=f"{service} API 오류: {message}",
            status_code=status_code,
            detail={"service": service},
        )

class ValidationError(AppError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            message=message,
            status_code=400,
            detail={"field": field} if field else {},
        )

class RateLimitError(AppError):
    def __init__(self, service: str, retry_after: int | None = None):
        super().__init__(
            message=f"{service} API 요청 한도 초과",
            status_code=429,
            detail={"service": service, "retry_after": retry_after},
        )
```

## FastAPI 예외 핸들러

### 글로벌 핸들러 등록

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(f"AppError: {exc.message} [{request.method} {request.url.path}]")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "detail": exc.detail,
        },
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "서버 내부 오류가 발생했습니다",
        },
    )
```

## 서비스 계층 에러 처리

### 외부 API 호출

```python
import httpx

async def fetch_steam_data(app_id: int) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://store.steampowered.com/api/appdetails",
                params={"appids": app_id},
            )
            response.raise_for_status()
            data = response.json()

            app_data = data.get(str(app_id), {})
            if not app_data.get("success"):
                raise NotFoundError("Steam 게임", app_id)

            return app_data["data"]

    except httpx.TimeoutException:
        raise ExternalAPIError("Steam", "요청 시간 초과")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimitError("Steam")
        raise ExternalAPIError("Steam", f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise ExternalAPIError("Steam", str(e))
```

### 데이터베이스 작업

```python
from sqlalchemy.exc import IntegrityError, NoResultFound

async def create_game(db: AsyncSession, data: GameCreate) -> Game:
    try:
        game = Game(**data.model_dump())
        db.add(game)
        await db.flush()
        await db.refresh(game)
        return game
    except IntegrityError as e:
        await db.rollback()
        if "steam_app_id" in str(e):
            raise ValidationError(f"이미 등록된 Steam 게임입니다 (app_id: {data.steam_app_id})")
        raise ValidationError("데이터 무결성 오류")
```

### AI API 호출

```python
import anthropic

async def analyze_with_claude(prompt: str) -> str:
    try:
        client = anthropic.AsyncAnthropic()
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except anthropic.RateLimitError:
        raise RateLimitError("Claude API", retry_after=60)
    except anthropic.APIError as e:
        raise ExternalAPIError("Claude API", str(e))
```

## 에러 응답 형식

### 일관된 에러 응답 구조

```json
{
    "error": "NotFoundError",
    "message": "Steam 게임을(를) 찾을 수 없습니다",
    "detail": {
        "resource": "Steam 게임",
        "id": "9999999"
    }
}
```

### HTTP 상태 코드 사용 규칙

| 코드 | 상황 | 예시 |
|------|------|------|
| 400 | 클라이언트 입력 오류 | 잘못된 URL 형식 |
| 404 | 리소스 없음 | 존재하지 않는 게임 ID |
| 409 | 충돌 | 이미 존재하는 데이터 |
| 422 | Pydantic 검증 실패 | FastAPI 자동 처리 |
| 429 | 요청 한도 | 외부 API rate limit |
| 502 | 외부 서비스 오류 | Steam API 실패 |
| 500 | 서버 내부 오류 | 예상치 못한 예외 |

## 로깅 전략

### 구조화된 로깅

```python
import logging
import structlog

logger = structlog.get_logger()

# 서비스 계층에서
logger.info("steam_api_call", app_id=app_id, duration_ms=elapsed)
logger.warning("rate_limit_hit", service="Steam", retry_after=60)
logger.error("analysis_failed", game_id=game_id, error=str(exc), exc_info=True)
```

### 로깅 레벨 기준

- `DEBUG`: 개발 중 디버깅 정보
- `INFO`: 정상 동작 추적 (API 호출, 분석 완료)
- `WARNING`: 복구 가능한 문제 (rate limit, 재시도)
- `ERROR`: 실패한 작업 (API 오류, DB 오류)
- `CRITICAL`: 서비스 불가 상태

## 재시도 패턴

### 지수 백오프

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
)
async def fetch_with_retry(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=15.0)
        response.raise_for_status()
        return response.json()
```

- 일시적 오류(타임아웃, 네트워크)만 재시도
- 비즈니스 로직 오류(404, 검증 실패)는 재시도하지 않음
- 최대 3회, 지수 백오프 적용

## 주의사항

- 예외 메시지에 시크릿(API 키, DB 비밀번호) 노출 금지
- `except Exception:` (bare except) 후 아무 처리 없이 pass 금지
- 로그에 사용자 개인정보 저장 금지
- 외부 API 에러를 그대로 클라이언트에 노출하지 않기
- 에러 응답은 항상 일관된 JSON 구조 유지
