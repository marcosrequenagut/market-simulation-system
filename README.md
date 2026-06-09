# 📈 Market Simulation System

A professional financial analysis and investment simulation API built with FastAPI, PostgreSQL, and Streamlit. The system fetches real market data for multiple indices, calculates key financial metrics, and runs Monte Carlo simulations to forecast portfolio evolution.

---

## 🗂️ Project Structure

```
market-simulation-system/
├── app/                        # FastAPI backend
│   ├── core/
│   │   ├── db.py               # SQLAlchemy engine and session
│   │   ├── models.py           # ORM models (MarketPrice)
│   │   └── queries.py          # Database query layer
│   ├── engine/
│   │   ├── calculator.py       # CAGR, compound interest
│   │   └── montecarlo.py       # Monte Carlo simulations
│   ├── routers/
│   │   ├── market.py           # Market data endpoints
│   │   ├── simulation.py       # Simulation endpoints
│   │   ├── metrics.py          # Metrics endpoints
│   │   └── compare.py          # Strategy comparison endpoints
│   ├── db/
│   │   └── init.sql            # Database schema reference
│   └── main.py                 # FastAPI app entry point
├── ingestion/
│   ├── main.py                 # Automatic data ingestion service
│   └── Dockerfile
├── frontend/
│   ├── app.py                  # Main Streamlit page (price charts)
│   ├── pages/
│   │   └── 1_Simulation.py     # Investment simulator page
│   └── Dockerfile
├── tests/
│   ├── test_api.py             # API endpoint tests
│   ├── test_calculator.py      # Calculator unit tests
│   ├── test_montecarlo.py      # Monte Carlo unit tests
│   ├── test_queries.py         # Database query tests (mocked)
│   └── test_market_router.py   # Market router tests (mocked)
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD pipeline
├── sonar-project.properties    # SonarCloud configuration
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Backend Dockerfile
└── requirements.txt
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  Ingestion  │    │   Backend   │    │  Frontend   │ │
│  │  Service    │    │   FastAPI   │    │  Streamlit  │ │
│  │             │───▶│   :8000     │◀───│   :8501     │ │
│  │ APScheduler │    │             │    │             │ │
│  └──────┬──────┘    └──────┬──────┘    └─────────────┘ │
│         │                  │                            │
│         ▼                  ▼                            │
│  ┌─────────────────────────────────────┐               │
│  │         PostgreSQL :5432            │               │
│  │         market_prices table         │               │
│  └─────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | FastAPI + Uvicorn | REST API |
| **Database** | PostgreSQL 16 | Market data storage |
| **ORM** | SQLAlchemy | Database abstraction |
| **Frontend** | Streamlit + Plotly | Interactive dashboards |
| **Ingestion** | yfinance + APScheduler | Automated data pipeline |
| **Containers** | Docker + Docker Compose | Service orchestration |
| **CI/CD** | GitHub Actions | Automated testing and linting |
| **Code Quality** | SonarCloud | Static analysis and coverage |
| **Project Mgmt** | Jira | Task and sprint management |
| **IDE** | Windsurf | AI-assisted development |

---

## 📊 Market Data

The system tracks **10 financial indices and assets**:

| Ticker | Name |
|---|---|
| `^GSPC` | S&P 500 |
| `^DJI` | Dow Jones Industrial Average |
| `^IXIC` | NASDAQ Composite |
| `^FTSE` | FTSE 100 |
| `^DAX` | DAX (Germany) |
| `^FCHI` | CAC 40 (France) |
| `^N225` | Nikkei 225 (Japan) |
| `^HSI` | Hang Seng (Hong Kong) |
| `GC=F` | Gold Futures |
| `BTC-USD` | Bitcoin |

### Database Schema

```sql
CREATE TABLE market_prices (
    date        DATE           NOT NULL,
    ticker      VARCHAR(20)    NOT NULL,
    open        DOUBLE PRECISION,
    high        DOUBLE PRECISION,
    low         DOUBLE PRECISION,
    close       DOUBLE PRECISION,
    volume      BIGINT,
    PRIMARY KEY (date, ticker)
);
```

---

## 🔄 Data Ingestion

The ingestion service runs automatically on startup and updates daily at 23:00:

```
On startup:
├── Table empty?  → Download full historical data (from 1927 for S&P 500)
└── Table exists? → Download only new data since last available date
```

This logic prevents duplicates regardless of how many times Docker is restarted.

---

## 🚀 Getting Started

### Prerequisites

- Docker Desktop
- Git

### Run the project

```bash
git clone https://github.com/marcosrequenagut/market-simulation-system.git
cd market-simulation-system
docker-compose up --build
```

Services will be available at:

| Service | URL |
|---|---|
| Frontend (Streamlit) | http://localhost:8501 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

> The ingestion service will automatically download historical data on first run. This may take a few minutes.

---

## 📡 API Endpoints

### Market Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/market/tickers` | List all available tickers |
| `GET` | `/market/{ticker}/latest` | Most recent price for a ticker |
| `GET` | `/market/{ticker}/prices` | Historical prices with optional filters |
| `GET` | `/market/{ticker}/history` | Price history by years or days |
| `GET` | `/market/{ticker}/returns` | Daily returns |
| `GET` | `/market/{ticker}/stats` | Annualized return, volatility and CAGR |

### Simulation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/simulate/` | Full portfolio simulation |

#### Simulation Request Body

```json
{
  "initial_investment": 10000,
  "monthly_contribution": 500,
  "annual_rate": 0.07,
  "annual_volatility": 0.15,
  "years": 20,
  "simulations": 1000,
  "model": "lognormal"
}
```

### Metrics & Comparison

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/metrics/` | CAGR, total return, Sharpe ratio |
| `POST` | `/compare/` | Compare multiple investment strategies |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |

---

## 🧮 Mathematical Engine

### CAGR (Compound Annual Growth Rate)

```
CAGR = (final_value / initial_value) ^ (1 / years) - 1
```

### Compound Interest with Monthly Contributions

Simulates monthly compounding with regular contributions:

```
balance = balance × (1 + monthly_rate) + monthly_contribution
```

Returns: `final_value`, `total_invested`, `total_interest`

### Monte Carlo Simulation

Two models available:

**Gaussian** — Basic model using normal distribution for yearly returns.

**Lognormal** (default) — Financially correct model that prevents negative portfolio values:

```
μ = log(1 + annual_return) - 0.5 × σ²
balance = balance × e^(monthly_return)
```

Returns percentiles: `p10` (pessimistic), `p50` (base), `p90` (optimistic)

### Annualized Metrics

Calculated from real historical data in the database:

- **Annual Return** = mean daily return × 252
- **Annual Volatility** = std daily return × √252
- **CAGR** = (last_price / first_price) ^ (1 / years) - 1

---

## 🖥️ Frontend

### Page 1 — Market Overview (`app.py`)

- Selector for all 10 indices
- Today's price and daily change with percentage
- Interactive price chart with Plotly
- Time range selector: 5 Days / 1 Month / 6 Months / 1 Year / 5 Years / 20 Years / Max
- Dynamic Y-axis scaling per time range

### Page 2 — Investment Simulator (`1_Simulation.py`)

- Ticker selector with automatic historical stats preloading
- Inputs: initial investment, monthly contribution, years, expected return
- Results: total invested, final value, ROI
- Monte Carlo scenarios: pessimistic (p10), base (p50), optimistic (p90)
- Portfolio evolution chart vs total invested

---

## ⚙️ CI/CD Pipeline

GitHub Actions runs on every push to `main` and `develop`:

```
push/PR
    ├── test   → pytest + coverage report
    ├── lint   → flake8 (PEP8 compliance)
    └── sonar  → SonarCloud analysis (needs test to pass first)
```

Coverage report is shared between `test` and `sonar` jobs via GitHub Actions artifacts.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_calculator.py -v
```

### Test Strategy

| Test File | What it tests | Approach |
|---|---|---|
| `test_calculator.py` | CAGR, compound interest | Unit tests with known values |
| `test_montecarlo.py` | Monte Carlo simulations | Unit tests with statistical validation |
| `test_api.py` | Core API endpoints | FastAPI TestClient |
| `test_queries.py` | Database query functions | Mocked SQLAlchemy session |
| `test_market_router.py` | Market router endpoints | TestClient + dependency override |

> Database tests use `unittest.mock.MagicMock` to simulate SQLAlchemy sessions, allowing tests to run without a real PostgreSQL instance (required for GitHub Actions).

---

## 📋 Jira Backlog

Project key: `MSS`

Commit convention:
```
git commit -m "MSS-{ticket_number}: description"
```

Example:
```
git commit -m "MSS-7: integrate yfinance for real S&P 500 data"
```

---

## 🔧 Development

### Local setup (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
source .venv/bin/activate       # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload

# Run frontend (separate terminal)
streamlit run frontend/app.py
```

> Note: requires a running PostgreSQL instance with the `market_data` database.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/market_data` | PostgreSQL connection string |

---

## 📁 Branch Strategy

```
main        ← production, protected
develop     ← integration branch
feature/*   ← individual features
```

SonarCloud analyzes `main` branch on the free plan.

---

## 🔮 Roadmap

- [ ] Multi-index comparison chart (normalized to base 100)
- [ ] Maximum drawdown metric
- [ ] Sharpe ratio per ticker
- [ ] Inflation-adjusted simulation
- [ ] Return distribution histogram (Monte Carlo PRO)
- [ ] Correlation matrix between indices
- [ ] Automatic insights per ticker
