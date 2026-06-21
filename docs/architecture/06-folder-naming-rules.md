# Folder Naming Rules

## General Conventions

### Directory Names
- Case: lowercase only
- Separator: hyphen-separated (kebab-case)
- Examples: trading-module, market-data, user-settings
- No spaces: Never use spaces in directory names

### File Names
- Case: lowercase
- Separator: underscore-separated (snake_case)
- Examples: order_service.py, market_data.py, trade_repository.py
- Extensions: .py for Python, .ts for TypeScript, .tsx for React components

### Python Package Names
- Case: lowercase
- Separator: underscore-separated (snake_case)
- Examples: trading_engine, market_data, risk_evaluator

## Backend Folder Naming

### Layer Directories
- domain/ - Domain layer
- application/ - Application layer
- infrastructure/ - Infrastructure layer
- presentation/ - Presentation layer

### Subdirectories
- entities/ - Entity classes (plural)
- value_objects/ - Value object classes (plural)
- services/ - Domain and application services
- repositories/ - Repository implementations
- exceptions/ - Exception classes
- events/ - Domain event classes

### Module-Specific Directories
- trading/, market_data/, portfolio/, risk/, ai/, user/, notification/
- Each module has its own subdirectory within layers

### File Names
- {entity_name}.py - Single entity definition
- {entity_name}_repository.py - Repository implementation
- {entity_name}_service.py - Service implementation
- {entity_name}_test.py - Test file

## Frontend Folder Naming

### Components
- Directory: kebab-case (order-form/)
- Component file: PascalCase (OrderForm.tsx)
- Index file: index.ts for clean imports

### Hooks
- Directory: hooks/ (flat structure)
- File: use-{feature}.ts (e.g., use-trading-data.ts)

### Pages
- Directory: pages/ (flat structure)
- File: {PageName}.tsx (PascalCase)

### Stores
- Directory: stores/ (flat structure)
- File: {feature}-store.ts (kebab-case)

### API
- Directory: api/
- File: client.ts, endpoints.ts

## Test Naming

### Backend Tests
- Directory: tests/
- Unit tests: tests/unit/{module}/{test_name}.py
- Integration tests: tests/integration/{module}/{test_name}.py
- E2E tests: tests/e2e/{test_name}.py

### Test File Names
- test_{module}_{feature}.py - e.g., test_order_execution.py
- conftest.py - Shared test configuration

### Frontend Tests
- Unit tests: Colocate with component: Component.test.tsx
- Integration tests: tests/integration/
- E2E tests: tests/e2e/

## Infrastructure Naming

### Docker
- backend.Dockerfile - Backend container
- frontend.Dockerfile - Frontend container
- docker-compose.yml - Production compose
- docker-compose.dev.yml - Development compose

### Nginx
- nginx.conf - Main configuration

### CI/CD
- .github/workflows/ci.yml - Continuous integration
- .github/workflows/cd.yml - Continuous deployment

## Anti-Patterns

### Forbidden
- CamelCase directories: TradingModule/, MarketData/
- Double underscores: __tests__/, __init__.py (except for package init)
- Starting with numbers: 1_trading/, 2_market_data/
- Generic names: utils/, helpers/, common/ (be specific)
- Abbreviations: mkt_data/, usr/, acct/ (use full names)
- Deep nesting: More than 4 levels deep

### Discouraged
- Generic services/ at root (use module-specific directories)
- models/ at root (place in module subdirectories)
- controllers/ (use api/ or bot/)
- views/ (use pages/ for frontend)

## Special Cases

### Initialization Files
- Python: __init__.py only where needed for package structure
- TypeScript: index.ts for clean exports

### Configuration Files
- pyproject.toml - Python project config
- package.json - Node.js config
- .env.example - Environment variable template
- docker-compose.yml - Container orchestration

### Test Fixtures
- tests/fixtures/ - Test data files
- tests/factories/ - Test data factories
