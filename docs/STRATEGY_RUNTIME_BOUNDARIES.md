# Strategy Runtime Boundaries

SimTradeLab executes strategy entry files in a restricted namespace. It blocks
the imports and built-ins listed below, but it is not a complete OS or network
security sandbox. The restriction makes common Python network clients
unavailable to strategy code; it does not claim process-level isolation against
every possible access path. Run untrusted code only inside an appropriately
isolated host environment.

These restrictions apply only to code loaded as a strategy by the backtest
engine; ordinary Python scripts run outside the restricted strategy environment
are not restricted by SimTradeLab. Download external datasets in a normal
host-side script before starting the backtest, store a fixed local copy, and let
the strategy consume that local, reproducible input through supported APIs. Do
not fetch live data from `initialize`, `handle_data`, or another strategy
callback.

The sandbox also removes the built-ins `exec`, `eval`, `compile`, and
`breakpoint`.

## Blocked top-level modules

- `os`
- `sys`
- `io`
- `subprocess`
- `shutil`
- `socket`
- `http`
- `urllib`
- `ctypes`
- `signal`
- `importlib`
- `runpy`
- `code`
- `codeop`

Imports are checked by their top-level name, so `urllib.request` is blocked by
the `urllib` entry and `http.client` is blocked by the `http` entry.

## Security code formats

Use the format expected by the API or data boundary you are interacting with.
SimTradeLab reuses its existing suffix normalization; this document does not
introduce another conversion layer.

| Example | Role | Usage |
| --- | --- | --- |
| `000300.XSHG` | Public PTrade-style security code | Accepted at public PTrade-compatible API boundaries and normalized internally. |
| `000300.SH` | Internal market-data security code | A short Shanghai suffix used by stock-oriented data sources; preserve the exact code present in that dataset. |
| `000300.SS` | Benchmark identifier and normalized index code | The SimTradeData/Pandas-style Shanghai index code used by the default CN benchmark and by `.XSHG` normalization. |

Do not assume that these three strings are interchangeable in arbitrary files.
Public strategy inputs may be normalized, while direct data dictionaries and
benchmark configuration must match the identifiers stored by their data source.

## API compatibility scope

The sandbox boundary is separate from API compatibility. See the
[PTrade backtest API support matrix](PTrade_Backtest_API_Support_Matrix.md) for
the current `full`, `partial`, `pending`, and `unsupported` classifications.
