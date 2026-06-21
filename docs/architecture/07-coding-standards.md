# Coding Standards

## Python Standards

### PEP 8 Compliance
- All code must pass ruff check with zero warnings
- Line length: 88 characters (Black/Ruff default)
- Indentation: 4 spaces (no tabs)
- Trailing commas in multi-line structures

### Type Hints
- Mandatory on all public function signatures
- Use from __future__ import annotations for forward references
- Prefer typing module over type comments
- Use Protocol for structural subtyping

### Docstrings
- Google-style format for all public APIs
- Required for: modules, classes, public functions, methods
- Minimum: one-line description for simple functions
- Include Args, Returns, Raises for complex functions

### Imports
- Standard library first
- Third-party libraries second
- Local modules last
- Use ruff or isort for import sorting
- No wildcard imports (from module import *)
- Group imports with blank lines between groups

### Formatting
- ruff format for code formatting
- isort for import sorting
- No trailing whitespace
- Single quotes preferred for strings (unless string contains single quote)
- f-strings for string formatting

## Async Coding Standards

### Async First
- All I/O operations must be async (database, HTTP, file system)
- Use async def for all I/O-bound functions
- Use def only for CPU-bound or sync-only code

### Concurrency Patterns
- asyncio.gather() for concurrent independent operations
- asyncio.create_task() for fire-and-forget tasks
- asyncio.Queue for producer-consumer patterns
- Structured concurrency preferred over bare tasks

### Error Handling
- Always await coroutines (never forget await)
- Use async with for async context managers
- Propagate exceptions; do not swallow
- Use try/except around awaited calls

### Synchronization
- Avoid shared mutable state
- Use asyncio.Lock for mutual exclusion
- Use asyncio.Event for signaling
- Prefer message passing over shared state

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | TradingEngine, RiskEvaluator |
| Functions | snake_case | execute_trade(), calculate_balance() |
| Variables | snake_case | portfolio_id, total_value |
| Constants | UPPER_CASE | MAX_RETRIES, DEFAULT_TIMEOUT |
| Private | _single_underscore | _internal_method() |
| Type aliases | PascalCase | Symbol = str |
| Enums | PascalCase | class OrderStatus(Enum) |

### Module Names
- Snake_case: trading_engine.py, market_data.py
- Descriptive: order_executor.py, not handler.py

### Private Conventions
- Single underscore: internal use within module
- Double underscore: name mangling (avoid unless needed)
- Leading underscore for unused arguments: _, status

## Frontend Coding Standards

### TypeScript
- Strict mode enabled (strict: true)
- No any types (use unknown with type guards)
- Explicit return types on functions
- Interfaces for object shapes, types for unions

### React Components
- Functional components only
- Props interfaces defined above component
- Hooks at top of component
- Early returns for conditional rendering
- Destructure props at top

### State Management
- Zustand or similar for global state
- React Query (TanStack) for server state
- Local state for UI-only concerns
- No Redux boilerplate (prefer simpler solutions)

### Styling
- TailwindCSS utility classes
- Component variants for complex styles
- No CSS modules or styled-components (by default)
- Responsive design with Tailwind breakpoints

### File Structure
- One component per file
- Co-locate related files
- Index files for clean exports
