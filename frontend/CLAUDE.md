# Frontend - Gametopia

## 기술 스택

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS v4
- **Package Manager**: pnpm

## 프로젝트 구조

```
src/
├── app/           # Next.js App Router 페이지
├── components/    # 재사용 가능한 UI 컴포넌트
│   ├── ui/        # 기본 UI 프리미티브 (Button, Input 등)
│   └── layouts/   # 레이아웃 컴포넌트 (Header, Sidebar 등)
├── lib/           # 유틸리티, API 클라이언트, 타입 정의
│   └── api.ts     # 백엔드 API 호출 래퍼
├── hooks/         # 커스텀 React 훅
└── types/         # 전역 TypeScript 타입
```

## 개발 가이드

- API 요청은 `src/lib/api.ts`의 클라이언트를 통해 수행
- 백엔드 API 프록시: `/api/*` → `localhost:8000/api/*`
- 환경변수: `NEXT_PUBLIC_API_URL` (기본값: http://localhost:8000)
- 컴포넌트는 Server Component를 기본으로 사용, 필요시 `"use client"` 명시

## 관련 문서

- @AGENTS.md — Next.js 버전 관련 주의사항
