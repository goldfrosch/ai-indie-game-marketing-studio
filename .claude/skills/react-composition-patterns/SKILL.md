---
name: vercel-composition-patterns
description: React composition patterns that scale. Use when refactoring components with boolean prop proliferation, building flexible component libraries, or designing reusable APIs. Triggers on tasks involving compound components, render props, context providers, or component architecture. Includes React 19 API changes.
license: MIT
metadata:
  author: vercel
  version: "1.0.0"
---

# React Composition Patterns

Composition patterns for building flexible, maintainable React components. Avoid boolean prop proliferation by using compound components, lifting state, and composing internals. These patterns make codebases easier for both humans and AI agents to work with as they scale.

## When to Apply

Reference these guidelines when:
- Refactoring components with many boolean props
- Building reusable component libraries
- Designing flexible component APIs
- Reviewing component architecture
- Working with compound components or context providers

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Component Architecture | HIGH | `architecture-` |
| 2 | State Management | MEDIUM | `state-` |
| 3 | Implementation Patterns | MEDIUM | `patterns-` |
| 4 | React 19 APIs | MEDIUM | `react19-` |

## Rules

### 1. Component Architecture (HIGH)

#### `architecture-avoid-boolean-props`
Don't add boolean props to customize behavior — use composition instead.

```tsx
// ❌ Boolean prop proliferation
<Button primary disabled loading icon="save" />

// ✅ Composition
<Button variant="primary">
  <Spinner />
  <SaveIcon />
  Save
</Button>
```

#### `architecture-compound-components`
Structure complex components with shared context.

```tsx
// ✅ Compound component pattern
<Tabs defaultValue="tab1">
  <Tabs.List>
    <Tabs.Trigger value="tab1">Tab 1</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="tab1">Content</Tabs.Content>
</Tabs>
```

### 2. State Management (MEDIUM)

#### `state-decouple-implementation`
The Provider is the only place that knows how state is managed.

```tsx
// ✅ State logic hidden in provider
function TabsProvider({ children, defaultValue }) {
  const [active, setActive] = useState(defaultValue)
  return <TabsContext value={{ active, setActive }}>{children}</TabsContext>
}
```

#### `state-context-interface`
Define a generic interface with state, actions, and meta for dependency injection.

```tsx
interface TabsContext {
  // state
  active: string
  // actions
  setActive: (value: string) => void
  // meta
  orientation: 'horizontal' | 'vertical'
}
```

#### `state-lift-state`
Move state into provider components for sibling access.

### 3. Implementation Patterns (MEDIUM)

#### `patterns-explicit-variants`
Create explicit variant components instead of boolean modes.

```tsx
// ❌ Boolean mode
<Alert error />
<Alert warning />

// ✅ Explicit variants
<AlertError />
<AlertWarning />
// or
<Alert variant="error" />
<Alert variant="warning" />
```

#### `patterns-children-over-render-props`
Use `children` for composition instead of `renderX` props.

```tsx
// ❌ Render prop
<Modal renderHeader={() => <h1>Title</h1>} />

// ✅ Children composition
<Modal>
  <Modal.Header>Title</Modal.Header>
  <Modal.Body>Content</Modal.Body>
</Modal>
```

### 4. React 19 APIs (MEDIUM)

> **⚠️ React 19+ only.** This project uses React 19.

#### `react19-no-forwardref`
Don't use `forwardRef` — refs are now plain props in React 19.

```tsx
// ❌ React 18 forwardRef
const Input = forwardRef<HTMLInputElement, InputProps>((props, ref) => (
  <input ref={ref} {...props} />
))

// ✅ React 19 — ref as prop
function Input({ ref, ...props }: InputProps & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />
}
```

#### `react19-use-hook`
Use `use()` instead of `useContext()` for reading context.

```tsx
// ❌ React 18
const theme = useContext(ThemeContext)

// ✅ React 19
const theme = use(ThemeContext)
```
