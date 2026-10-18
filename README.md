# 📈 Qviser: Quantitative Algorithmic Trading Co-Pilot

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Qviser** (**Q**uant + Ad**viser**) is a modular, high-performance Python co-assisting engine designed to support manual, hybrid, and semi-automated quantitative trading workflows. 

Rather than functioning as a black-box execution bot, **Qviser** acts as an intelligent co-pilot: continuously streaming market data, validating complex multi-timeframe setups, enforcing strict risk rules, and routing execution signals with low latency.

---

## 🎯 Key Features

- 🔍 **Multi-Timeframe Setup Evaluator:** Continuously computes VWAP standard deviation bands, volume profiles, MACD/RSI scans, and order flow delta dynamics in real time.
- 🛡️ **Algorithmic Risk Gatekeeper:** Pre-trade validation enforcing strict risk-per-trade limits, position sizing calculations, and hard daily drawdown stops before order routing.
- ⚡ **Co-Pilot & Automated Modes:** Operates seamlessly in advisory mode (pushing real-time setup alerts to Telegram/Discord) or full co-pilot mode (assisted or automated broker order placement).
- 📊 **Telemetry & Observability:** Integrated logging and OpenTelemetry tracing for low-latency strategy evaluation, execution tracking, and performance metrics.
- 🧪 **Backtest & Paper Trading Engine:** Test strategies against historical tick data or run live paper-trading simulations before deploying real capital.

---

## 🏗️ Project Architecture

```text
               ┌───────────────────────────────┐
               │    Market Data Feed / Websocket│
               └───────────────┬───────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Qviser Core Engine                       │
│                                                             │
│  ┌────────────────────┐         ┌────────────────────────┐  │
│  │   Feature Engine   │ ──────► │    Setup Evaluator     │  │
│  │ (VWAP, Delta, RSI) │         │ (Rule & Signal Engine) │  │
│  └────────────────────┘         └───────────┬────────────┘  │
│                                             │               │
│                                             ▼               │
│                                 ┌────────────────────────┐  │
│                                 │     Risk Gatekeeper    │  │
│                                 │ (Sizing & Limits Check)│  │
│                                 └───────────┬────────────┘  │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
                       ▼                                             ▼
         ┌───────────────────────────┐                 ┌───────────────────────────┐
         │ Alerts & Notifications    │                 │ Execution Router          │
         │ (Telegram / Webhooks / UI)│                 │ (Broker APIs / Paper)     │
         └───────────────────────────┘                 └───────────────────────────┘
```

---

## 📂 Repository Layout

```text
qviser/
├── config/                  # Strategy profiles and broker configuration
│   ├── default_config.yaml
│   └── risk_limits.yaml
├── src/
│   └── qviser/
│       ├── __init__.py
│       ├── main.py          # CLI entry point (`qviser` command → qviser.main:main)
│       ├── engine.py        # Core event loop and orchestration
│       ├── features/        # Technical analysis, VWAP, and order flow calculations
│       │   ├── indicators.py
│       │   └── order_flow.py
│       ├── strategies/      # Custom strategy and setup logic
│       │   ├── base.py
│       │   └── vwap_reversion.py
│       ├── risk/            # Risk parameters, drawdown monitor, and position sizing
│       │   └── gatekeeper.py
│       ├── execution/       # Broker API connectors and paper trader
│       │   ├── broker_base.py
│       │   └── paper_trader.py
│       └── utils/           # Logging, telemetry, and formatting helpers
│           ├── logger.py
│           └── telemetry.py
├── tests/                   # Unit and integration tests
├── .python-version          # Python version pinned for uv
├── pyproject.toml           # Project metadata, dependencies, and build system (uv_build)
├── uv.lock                  # Locked dependency versions (commit this file)
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **[uv](https://docs.astral.sh/uv/)**: the Python package and project manager used by this repo
- **Python 3.11+**: uv installs the version pinned in `.python-version` for you if it's missing

Install uv if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with Homebrew
brew install uv
```

### 1. Installation

Clone the repository and sync the environment:

```bash
git clone https://github.com/your-username/qviser.git
cd qviser

# Creates .venv, installs the pinned Python, all locked dependencies,
# and qviser itself in editable mode
uv sync
```

You don't need to activate a virtual environment. Prefix commands with `uv run` and they run inside the project's `.venv` automatically.

> **Note:** If you have another virtualenv active (e.g. pyenv or conda), uv warns that `VIRTUAL_ENV` doesn't match `.venv` and ignores it. Run `deactivate` first to get rid of the warning.

### 2. Managing Dependencies

```bash
uv add pandas numpy              # Add runtime dependencies
uv add --dev pytest ruff         # Add development-only dependencies
uv remove <package>              # Remove a dependency
uv lock --upgrade                # Upgrade all locked versions
uv sync --locked                 # Install exactly what uv.lock specifies (use in CI)
```

`uv add` and `uv remove` update both `pyproject.toml` and `uv.lock`. Commit both files.

### 3. Configuration

Copy the sample environment file and set up your trading configuration:

```bash
cp config/default_config.yaml config/local_config.yaml
```

Update `local_config.yaml` with your preferred symbols, indicator settings, and risk thresholds.

---

## 💻 Usage Example

Here is a quick Python example of running **Qviser** in co-pilot advisory mode:

```python
from qviser.engine import QviserEngine
from qviser.risk.gatekeeper import RiskGatekeeper
from qviser.strategies.vwap_reversion import VWAPReversionStrategy

# Initialize Risk Gatekeeper (Max 1% risk per trade, 3% max daily drawdown)
risk_guard = RiskGatekeeper(
    max_risk_per_trade_pct=1.0,
    max_daily_drawdown_pct=3.0,
    max_open_positions=3
)

# Initialize Strategy
strategy = VWAPReversionStrategy(std_dev_band=2.0, rsi_period=14)

# Create Qviser Instance
app = QviserEngine(
    symbol="NIFTY50",
    timeframe="5m",
    strategy=strategy,
    risk_gatekeeper=risk_guard,
    mode="copilot"  # Options: 'copilot' (Alerts), 'automated' (Direct Orders)
)

# Start Co-Pilot Scan Loop
if __name__ == "__main__":
    app.start()
```

### CLI Command

Run a script inside the project environment:

```bash
uv run python examples/copilot.py
```

### CLI Command

The `qviser` command is registered via `[project.scripts]` in `pyproject.toml`. Start the engine with:

```bash
uv run qviser run --config config/local_config.yaml --mode copilot
```

---

## 🧪 Running Tests

Ensure all unit tests and risk rule validations pass before deployment:

```bash
uv add --dev pytest   # one-time setup
uv run pytest tests/ -v
```

---

## ⚙️ Tech Stack & Dependencies

- **Data Processing:** `pandas`, `numpy`, `scipy`
- **Indicators & Strategy:** `TA-Lib`, `pandas-ta`
- **Concurrency & Async:** `asyncio`, `celery`, `redis`
- **Broker API:** `dhanhq`
- **Observability:** `opentelemetry-api`, `loguru`
- **Packaging & Environment:** [`uv`](https://docs.astral.sh/uv/) with the `uv_build` backend (`src/` layout)

### Building a Distribution

```bash
uv build   # writes the sdist and wheel to dist/
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.