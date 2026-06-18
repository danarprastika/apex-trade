# Strategy Plugin System Design for APEX

## Overview

This document outlines the design for a Strategy Plugin System that extends APEX's existing trading architecture to support pluggable strategy implementations with proper versioning, configuration, and lifecycle management.

---

## 1. Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                          │
│   /api/v1/strategies/*, /api/v1/signals/*, /api/v1/orders/*      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Strategy Engine (Core)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Plugin Registry │  │ Strategy Router │  │ Strategy Runner │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Strategy Plugins                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ Trend      │ │ Mean       │ │ Breakout   │ │ Scalping   │     │
│  │ Following  │ │ Reversion  │ │            │ │            │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Custom User Strategies (Sandboxed)                  │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Shared Services                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ Market     │ │ Risk       │ │ Portfolio  │ │ Execution  │     │
│  │ Data       │ │ Service    │ │ Service    │ │ Service    │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **Plugin Interface** | Defines the contract all strategy plugins must implement |
| **Plugin Loader** | Dynamically loads/unloads plugin modules at runtime |
| **Plugin Registry** | Maintains registry of loaded plugins, their metadata, and versions |
| **Strategy Router** | Routes market data to appropriate strategy plugins based on type |
| **Strategy Runner** | Executes strategy logic and produces signals |
| **Configuration Manager** | Handles strategy parameters and user customizations |

### 1.3 Integration Points

- **Market Data Flow**: Market collector → Strategy Router → Active Strategies → Signal Service
- **Signal Flow**: Strategy Runner → Signal Service → Risk Service → Execution Service
- **Configuration Flow**: Config Manager ↔ Database ↔ Plugin Loader

---

## 2. Strategy Interface

### 2.1 Core Interface (ABC)

```python
# app/domain/strategies/base.py

class StrategyPlugin(ABC):
    """Abstract base class for all strategy plugins."""
    
    @property
    @abstractmethod
    def metadata(self) -> StrategyMetadata:
        """Returns plugin metadata including name, version, type."""
        pass
    
    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize strategy with configuration parameters. Called once on load."""
        pass
    
    @abstractmethod
    def analyze(self, market_data: MarketData) -> SignalResult | None:
        """Analyze market data and produce trading signal if conditions met."""
        pass
    
    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        """Validate configuration before initialization."""
        pass
    
    def on_market_update(self, market_data: MarketData) -> None:
        """Optional: Called for real-time bar-by-bar updates."""
        pass
    
    def on_signal_ack(self, signal_id: str) -> None:
        """Optional: Callback when signal is acknowledged by execution."""
        pass
    
    def get_parameters_schema(self) -> dict[str, Any]:
        """Returns JSON Schema for configuration validation."""
        pass
```

### 2.2 Data Structures

```python
# app/domain/strategies/types.py

@dataclass
class StrategyMetadata:
    name: str
    version: str
    strategy_type: StrategyType
    description: str
    author: str
    min_lookback_periods: int
    supported_assets: list[str]
    supported_timeframes: list[str]

@dataclass  
class SignalResult:
    signal_type: SignalType  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reason: str
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    metadata: dict[str, Any]

@dataclass
class ConfigValidation:
    valid: bool
    errors: list[str]
```

### 2.3 Strategy Type Enum Extension

Extend existing `StrategyType` enum to include:
- `trend_following` - Identifies trending markets and follows momentum
- `mean_reversion` - Capitalizes on price reverting to mean values
- `breakout` - Enters on breakout of support/resistance levels
- `scalping` - High-frequency micro-opportunities
- `custom` - User-defined sandboxed strategies

---

## 3. Plugin Loading System

### 3.1 Plugin Discovery

**Built-in Plugins Location**: `backend/plugins/`
```
plugins/
├── __init__.py
├── trend_following/
│   ├── __init__.py
│   ├── plugin.py          # Main strategy class
│   ├── indicators.py      # Strategy-specific indicators
│   └── params.py          # Parameter definitions
├── mean_reversion/
│   ├── __init__.py
│   └── plugin.py
├── breakout/
├── scalping/
└── custom/
    └── sandbox.py         # Secure sandboxed execution
```

### 3.2 Loading Mechanism

**Loading Modes**:
1. **Built-in**: Loaded from `plugins/` directory at startup
2. **User-uploaded**: Loaded from database-stored code (sandboxed)
3. **External**: Installed via pip (future extensibility)

**Plugin Lifecycle**:
```
1. DISCOVER: Scan plugin directories for valid plugin modules
2. VALIDATE: Check plugin meets interface requirements
3. LOAD: Import module and instantiate plugin class
4. REGISTER: Add to registry with metadata
5. INITIALIZE: Call initialize() with configuration
6. ACTIVATE: Mark as active for routing
7. EXECUTE: Process market data through analyze()
8. UNREGISTER: Remove on shutdown/error
```

### 3.3 Plugin Registry

```python
# app/services/plugin_registry.py

class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, StrategyPlugin] = {}  # code -> plugin
        self._by_type: dict[StrategyType, list[StrategyPlugin]] = {}
        self._active_plugins: set[str] = set()
    
    def register(self, plugin: StrategyPlugin) -> None:
        # Add to registry with metadata validation
    
    def unregister(self, code: str) -> None:
        # Remove plugin from registry
    
    def get_plugin(self, code: str) -> StrategyPlugin | None:
        # Retrieve plugin by code
    
    def get_plugins_by_type(self, strategy_type: StrategyType) -> list[StrategyPlugin]:
        # Get all plugins of a specific type
    
    def activate(self, code: str) -> None:
        # Mark plugin as active
    
    def deactivate(self, code: str) -> None:
        # Mark plugin as inactive
```

### 3.4 Sandboxed Execution for Custom Strategies

**Security Measures**:
- Use `RestrictedPython` or `pyodide` for user code isolation
- Time-boxed execution (max 100ms per analyze call)
- Memory limits (max 64MB per plugin)
- No filesystem/network access
- Whitelisted imports only (pandas, numpy, ta-lib subset)

---

## 4. Versioning Strategy

### 4.1 Semantic Versioning

Format: `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)

- **MAJOR**: Breaking API changes, incompatible parameter schema
- **MINOR**: New features, backward-compatible parameter additions
- **PATCH**: Bug fixes, performance improvements

### 4.2 Version Storage

**Database**: Store in `Strategy.version` field and `StrategyParameterSchema` table

**Schema Migration Table**:
```python
class StrategyParameterSchema(Base):
    __tablename__ = "strategy_parameter_schemas"
    
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"))
    version: Mapped[str]
    parameters_schema: Mapped[dict]  # JSON schema
    created_at: Mapped[datetime]
    migrated_from: Mapped[str | None]
```

### 4.3 Version Compatibility

- Each strategy plugin defines minimum compatible version
- Migrations auto-generate for MINOR/PATCH updates
- MAJOR updates require explicit configuration upgrade

### 4.4 Hot Reload Support

- Watch plugin directory for changes
- Graceful reload: drain current calls, load new version, route new data
- Rollback on failure: revert to previous version

---

## 5. Configuration Management

### 5.1 Configuration Layers

```
1. Default Parameters (hardcoded in plugin)
   ↓
2. System-wide Overrides (config files)
   ↓
3. User-specific Overrides (database)
   ↓
4. Runtime Overrides (API/UI)
```

### 5.2 Configuration Schema

Each strategy defines JSON Schema for parameters:

```json
{
  "type": "object",
  "properties": {
    "indicators": {
      "type": "array",
      "items": {"enum": ["ema", "sma", "rsi", "macd"]}
    },
    "entry_threshold": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "risk_multiplier": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 5.0
    }
  },
  "required": ["indicators", "entry_threshold"]
}
```

### 5.3 Runtime Configuration API

```
GET    /api/v1/strategies/{code}/config     # Get current config
PUT    /api/v1/strategies/{code}/config     # Update config
GET    /api/v1/strategies/{code}/schema     # Get parameter schema
POST   /api/v1/strategies/{code}/reset      # Reset to defaults
```

### 5.4 Configuration Validation Flow

1. Schema validation on write
2. Parameter constraint check (ranges, enums)
3. Cross-parameter validation (entry < take_profit)
4. Strategy-specific `validate_config()` hook
5. Persist to `StrategyParameter` table

---

## 6. Testing Strategy

### 6.1 Test Categories

| Category | Description | Target Coverage |
|----------|-------------|---------------|
| **Unit Tests** | Individual strategy plugins in isolation | 90%+ per plugin |
| **Integration Tests** | Plugin + Registry + Config Manager | 85% |
| **Sandboxed Tests** | Custom strategy execution safety | All security measures |
| **Performance Tests** | Latency under load | <100ms per analyze |

### 6.2 Testing Structure

```
tests/
├── unit/
│   ├── test_trend_following_plugin.py
│   ├── test_mean_reversion_plugin.py
│   ├── test_breakout_plugin.py
│   ├── test_scalping_plugin.py
│   └── test_plugin_registry.py
├── integration/
│   ├── test_strategy_engine.py
│   ├── test_plugin_lifecycle.py
│   └── test_config_manager.py
├── security/
│   └── test_sandbox_isolation.py
└── conftest.py
```

### 6.3 Test Data Strategy

- **Mock Market Data**: Synthetic OHLCV with known patterns
- **Historical Backtesting**: Real market data from database
- **Edge Cases**: Missing data, invalid inputs, extreme volatility
- **Concurrency**: Multiple plugins analyzing same data

### 6.4 Test Fixtures

```python
@pytest.fixture
def trend_strategy():
    plugin = TrendFollowingPlugin()
    plugin.initialize({"indicators": ["ema", "macd"], "timeframe": "1h"})
    return plugin

@pytest.fixture
def registry():
    return PluginRegistry()

@pytest.fixture
def sample_market_data():
    return MarketData(
        symbol="BTCUSDT",
        timeframe="1h",
        candles=[...],  # OHLCV data
        indicators={...}
    )
```

### 6.5 CI/CD Integration

- Run unit tests on every PR
- Integration tests on merge to main
- Performance benchmarks track regressions
- Security scan for sandbox escape attempts

---

## Implementation Phases

### Phase 1: Core Interface & Registry
- Define `StrategyPlugin` ABC
- Create `PluginRegistry` service
- Implement built-in plugin structure

### Phase 2: Built-in Strategies
- Implement Trend Following plugin
- Implement Mean Reversion plugin
- Implement Breakout plugin
- Implement Scalping plugin

### Phase 3: Configuration & Versioning
- Add parameter schema support
- Implement version migration
- Add hot reload capability

### Phase 4: Custom Strategy Sandbox
- Integrate RestrictedPython sandbox
- Add security validation
- Expose custom strategy API

### Phase 5: Testing & Documentation
- Comprehensive test suite
- Plugin development guide
- API documentation

---

## Risks & Considerations

| Risk | Mitigation |
|------|-----------|
| Custom strategy security | Sandboxed execution, code review, rate limiting |
| Plugin version conflicts | Semantic versioning, migration system |
| Performance impact | Async execution, caching, performance tests |
| Strategy instability | Health checks, circuit breakers, auto-disable |