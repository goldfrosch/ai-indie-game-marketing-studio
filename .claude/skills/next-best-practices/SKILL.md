---
name: next-best-practices
description: Next.js best practices - file conventions, RSC boundaries, data patterns, async APIs, metadata, error handling, route handlers, image/font optimization, bundling
user-invocable: false
---

# Next.js Best Practices

Apply these rules when writing or reviewing Next.js code.

## File Conventions

- Project structure and special files
- Route segments (dynamic, catch-all, groups)
- Parallel and intercepting routes
- Middleware rename in v16 (middleware → proxy)

## RSC Boundaries

Detect invalid React Server Component patterns:
- Async client component detection (invalid)
- Non-serializable props detection
- Server Action exceptions

## Async Patterns

Next.js 15+ async API changes:
- Async `params` and `searchParams`
- Async `cookies()` and `headers()`

```typescript
// ❌ Old sync pattern
export default function Page({ params }: { params: { id: string } }) {
  const id = params.id
}

// ✅ New async pattern (Next.js 15+)
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
}
```

## Runtime Selection

- Default to Node.js runtime
- Use Edge runtime only for: geolocation, low-latency responses, minimal compute

```typescript
// Edge runtime (opt-in only)
export const runtime = 'edge'
```

## Directives

- `'use client'` — React client boundary (browser APIs, state, effects)
- `'use server'` — React Server Actions
- `'use cache'` — Next.js caching directive

Rules:
- Place `'use client'` as close to leaf components as possible
- Never use `'use client'` in layout.tsx unless necessary
- Server Actions must be `async` functions

## Functions

### Navigation hooks (Client only)
```typescript
import { useRouter, usePathname, useSearchParams, useParams } from 'next/navigation'
```

### Server functions
```typescript
import { cookies, headers, draftMode, after } from 'next/headers'
// All must be awaited in Next.js 15+
const cookieStore = await cookies()
```

### Generate functions
```typescript
export async function generateStaticParams() { ... }
export async function generateMetadata({ params }): Promise<Metadata> { ... }
```

## Error Handling

```
app/
├── error.tsx          # Segment-level errors
├── global-error.tsx   # Root layout errors
└── not-found.tsx      # 404 pages
```

```typescript
import { redirect, permanentRedirect, notFound } from 'next/navigation'
import { forbidden, unauthorized } from 'next/navigation'  // auth errors
```

- Use `unstable_rethrow` in catch blocks to re-throw Next.js internal errors

## Data Patterns

| Pattern | Use When |
|---------|----------|
| Server Components | Reading data, no interactivity |
| Server Actions | Mutations, form submissions |
| Route Handlers | Webhooks, external API endpoints |

Avoid data waterfalls:
```typescript
// ✅ Parallel fetching
const [user, posts] = await Promise.all([getUser(id), getPosts(id)])
```

Client component data fetching: use SWR or React Query.

## Route Handlers

```typescript
// app/api/route.ts
export async function GET(request: Request) {
  return Response.json({ data: '...' })
}
```

- `GET route.ts` conflicts with `page.tsx` in same segment — avoid
- No React DOM available in route handlers
- Prefer Server Actions over Route Handlers for mutations

## Metadata & OG Images

```typescript
// Static
export const metadata: Metadata = { title: 'Page Title' }

// Dynamic
export async function generateMetadata({ params }): Promise<Metadata> {
  return { title: `Game: ${(await params).id}` }
}
```

OG image: use `next/og` with `ImageResponse`.

## Image Optimization

```typescript
import Image from 'next/image'

// ✅ Always use next/image
<Image src="/hero.png" alt="Hero" width={800} height={400} priority />
// Never use <img> directly
```

- Configure `remotePatterns` in `next.config.ts` for external images
- Use `priority` for above-the-fold images (LCP)
- Add `sizes` for responsive images

## Font Optimization

```typescript
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function Layout({ children }) {
  return <html className={inter.className}>{children}</html>
}
```

## Bundling

- Use `import()` for server-incompatible packages
- CSS: `import './styles.css'` not `<link>` tags
- Polyfills already included — don't add them manually
- Avoid ESM/CommonJS mixing

## Hydration Errors

Common causes:
- Browser-only APIs in server render (`window`, `document`)
- Dynamic content (dates, random values)
- Invalid HTML nesting

Fix with `suppressHydrationWarning` or `useEffect` for client-only values.

## Suspense Boundaries

Hooks requiring Suspense:
- `useSearchParams()` — wrap page in `<Suspense>`
- `usePathname()` in some patterns

```typescript
export default function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <SearchComponent />
    </Suspense>
  )
}
```

## Parallel & Intercepting Routes

```
app/
├── @modal/
│   └── (.)photo/[id]/
│       └── page.tsx    # Intercepted modal
└── photo/[id]/
    └── page.tsx        # Full page
```

- Add `default.tsx` as fallback for slots
- Close modals with `router.back()`

## Self-Hosting

```javascript
// next.config.ts
export default { output: 'standalone' }
```

- Configure cache handlers for multi-instance ISR
