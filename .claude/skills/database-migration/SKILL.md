---
name: database-migration
description: Alembic 기반 데이터베이스 마이그레이션 관리 가이드
---

# 데이터베이스 마이그레이션

Alembic을 사용한 DB 스키마 버전 관리 가이드입니다.

## 초기 설정

### Alembic 초기화

```bash
cd backend
uv run alembic init alembic
```

### alembic.ini 설정

```ini
# alembic.ini - sqlalchemy.url은 env.py에서 동적으로 설정
[alembic]
script_location = alembic
# sqlalchemy.url = ...  # env.py에서 설정하므로 주석 처리
```

### env.py 설정

```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.db.database import Base
from app.models import game  # 모든 모델 임포트 (메타데이터 등록용)

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## 마이그레이션 워크플로우

### 새 마이그레이션 생성

```bash
# 모델 변경 후 자동 감지로 리비전 생성
uv run alembic revision --autogenerate -m "add streamer table"

# 빈 리비전 생성 (수동 작성)
uv run alembic revision -m "seed game genres"
```

### 실행 및 관리

```bash
# 최신 버전으로 업그레이드
uv run alembic upgrade head

# 한 단계 업그레이드
uv run alembic upgrade +1

# 한 단계 다운그레이드 (롤백)
uv run alembic downgrade -1

# 특정 리비전으로 이동
uv run alembic upgrade abc123

# 현재 버전 확인
uv run alembic current

# 마이그레이션 히스토리
uv run alembic history

# SQL만 출력 (실행하지 않음)
uv run alembic upgrade head --sql
```

## 마이그레이션 파일 작성

### autogenerate 결과 검토

```python
# alembic/versions/001_add_streamer_table.py
"""add streamer table

Revision ID: abc123def456
Revises: 001_initial
Create Date: 2026-04-01 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision 식별자
revision: str = 'abc123def456'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'streamers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('channel_url', sa.String(500), nullable=False),
        sa.Column('subscriber_count', sa.Integer()),
        sa.Column('genres', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_streamers_platform', 'streamers', ['platform'])

def downgrade() -> None:
    op.drop_index('ix_streamers_platform')
    op.drop_table('streamers')
```

### 데이터 마이그레이션

```python
def upgrade() -> None:
    # 스키마 변경
    op.add_column('games', sa.Column('tags_array', sa.JSON(), nullable=True))

    # 데이터 변환 (기존 tags 문자열 → JSON 배열)
    conn = op.get_bind()
    games = conn.execute(sa.text("SELECT id, tags FROM games")).fetchall()
    for game in games:
        if game.tags:
            tag_list = [t.strip() for t in game.tags.split(",")]
            conn.execute(
                sa.text("UPDATE games SET tags_array = :tags WHERE id = :id"),
                {"tags": json.dumps(tag_list), "id": game.id},
            )

    # 기존 컬럼 삭제
    op.drop_column('games', 'tags')
    op.alter_column('games', 'tags_array', new_column_name='tags')
```

## 안전한 마이그레이션 원칙

### 비파괴적 변경 우선

```python
# ✅ 안전: 컬럼 추가 (nullable)
op.add_column('games', sa.Column('new_field', sa.String(100), nullable=True))

# ⚠️ 주의: NOT NULL 컬럼 추가 (기본값 필요)
op.add_column('games', sa.Column('status', sa.String(20), nullable=False, server_default='active'))

# ❌ 위험: 컬럼 삭제 (다른 단계에서 수행)
# Step 1: 코드에서 해당 컬럼 사용 중지
# Step 2: (다음 릴리즈) 컬럼 삭제 마이그레이션
```

### 다단계 마이그레이션

```python
# 마이그레이션 1: 새 컬럼 추가
def upgrade():
    op.add_column('games', sa.Column('price_krw', sa.Float(), nullable=True))

# 마이그레이션 2: 데이터 이관 (별도 리비전)
def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE games SET price_krw = price * 1300 WHERE price IS NOT NULL"))

# 마이그레이션 3: 제약조건 추가 (별도 리비전)
def upgrade():
    op.alter_column('games', 'price_krw', nullable=False)
    op.drop_column('games', 'price')
```

### SQLite 제약사항 회피

```python
# SQLite은 ALTER TABLE 제한이 많음 → 배치 마이그레이션 사용
with op.batch_alter_table('games') as batch_op:
    batch_op.alter_column('name', nullable=False)
    batch_op.add_column(sa.Column('new_col', sa.String(50)))
    batch_op.drop_column('old_col')
```

## 모델 변경 체크리스트

1. **모델 변경** → `models/game.py` 등에서 SQLAlchemy 모델 수정
2. **리비전 생성** → `alembic revision --autogenerate -m "설명"`
3. **결과 검토** → 생성된 마이그레이션 파일에서 `upgrade()` / `downgrade()` 확인
4. **로컬 테스트** → `alembic upgrade head` 실행 후 DB 확인
5. **롤백 테스트** → `alembic downgrade -1` 후 `alembic upgrade head` 재실행
6. **커밋** → 마이그레이션 파일과 모델 변경을 같이 커밋

## 자주 하는 실수

### 모델 임포트 누락

```python
# ❌ env.py에서 모델을 임포트하지 않으면 autogenerate가 변경을 감지하지 못함
# ✅ 모든 모델 파일을 env.py에서 임포트
from app.models import game, analysis, streamer  # 모델 메타데이터 등록
```

### 마이그레이션 충돌

```bash
# 여러 브랜치에서 마이그레이션 생성 시 충돌 발생
# 병합 후 리비전 정렬
uv run alembic merge heads -m "merge migrations"
```

### 데이터 손실 방지

```python
# ❌ 컬럼 삭제 전 데이터 백업 없음
def downgrade():
    op.drop_column('games', 'important_data')  # 복구 불가!

# ✅ 삭제 전 백업 테이블 생성
def upgrade():
    op.rename_table('games', '_games_backup_20260401')
    op.create_table('games', ...)
    # 데이터 복사...
```

## 프로덕션 배포 시

```bash
# 배포 전: SQL 미리보기
alembic upgrade head --sql > migration.sql

# 배포: 백업 후 실행
alembic upgrade head

# 문제 발생시: 즉시 롤백
alembic downgrade -1
```
