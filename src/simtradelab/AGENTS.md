# SimTradeLab - Core Framework

**Generated**: 2025-01-05  
**Python**: 3.12+ (framework only)  
**Purpose**: Local backtesting engine and PTrade API implementation

## OVERVIEW
Core backtesting framework providing PTrade API compatibility and local testing capabilities.

## STRUCTURE
```
simtradelab/
├── backtest/             # Backtesting engine core
├── ptrade/               # PTrade API mock implementation
├── research/             # Research utilities
├── service/              # Service layer components
├── trading/              # Trading execution logic
└── utils/                # Utility functions
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| PTrade API | `ptrade/api.py` | Main PtradeAPI class implementation |
| Strategy validation | `ptrade/strategy_validator.py` | Lifecycle + Python 3.5 checks |
| Backtesting core | `backtest/engine.py` | Local simulation engine |
| Python 3.5 checker | `utils/py35_compat_checker.py` | Compatibility validation |
| Performance tools | `utils/perf.py` | Timing and optimization utilities |

## CONVENTIONS
- **Type annotations allowed**: Python 3.12+ features enabled
- **F-strings allowed**: Modern Python syntax throughout
- **Future imports**: Use `from __future__ import annotations`
- **Logging**: Structured logging with context

## ANTI-PATTERNS
- **No direct database access**: Use data layer abstractions
- **No blocking I/O**: Async patterns for data fetching
- **No hardcoded paths**: Use configurable data directories
- **No production deployment**: Local development only