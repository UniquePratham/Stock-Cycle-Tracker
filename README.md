# Stock Cycle Tracker

A research-driven stock cycle analysis application built in Python using the **Rio UI** framework, **Pandas**, **Plotly**, and **SQLite**.

---

## 1. Overview & Core Concept

**Stock Cycle Tracker** tracks and evaluates recurring annual market cycles anchored to user-defined historical research dates (Last Dates / LD).

### How the Calculation Works:
1. **User Research Date (LD)**: The researcher inputs a stock symbol (e.g. `RELIANCE`) and a historically significant date (e.g. `10-Jan-2014`).
2. **Annual Recurrence**: The day and month (`10 January`) define the recurring annual reference date. The original year (`2014`) is preserved for context.
3. **Non-Trading Day Resolution**: If `10 January` falls on a weekend or market holiday, the engine automatically resolves to the **next available trading day** (e.g. `12-Jan-2026`).
4. **Reference High**: The reference point is strictly the **High price of that resolved trading day**.
5. **Cycle Boundaries**: The cycle runs from the current annual reference date until the day before the next annual reference date (`10-Jan-2026` → `09-Jan-2027`).
6. **Price Modes**:
   - **LIVE**: Current market price during open market hours (09:15–15:30 IST).
   - **CLOSE**: Latest closing price after market hours.
7. **Percentage Change**:
   $$\text{Percentage Change} = \left(\frac{\text{Current Price} - \text{Reference High}}{\text{Reference High}}\right) \times 100$$
8. **Predefined Buckets**:
   - **Upside**: `+5–10%`, `+10–15%`, `+15–20%`, `>+20%`
   - **Downside**: `-5–10%`, `-10–15%`, `-15–20%`, `<-20%`
   - **Neutral**: `Within ±5% / Unclassified`

---

## 2. Key Features

- **Multiple Stocks & Multiple Independent Cycles**: Track `RELIANCE Cycle 1 (10-Jan-2014)`, `Cycle 2 (30-Jan-2016)`, etc., simultaneously.
- **Exchange Preference**: Resolves via **NSE** first, **BSE** second, and fallback third.
- **Rio Web UI**: Clean, research-oriented dashboard with interactive search, filters, metrics, and stock cycle management.
- **Plotly Visualizations**: Interactive price charts displaying historical prices, reference High dashed lines, and reference date markers.
- **Bulk Excel Ingestion & Export**: Upload spreadsheets with `Stock Name` and `Reference Date`, and export full 18-column analytical reports.
- **Rule-Based Alerts**: Set triggers on percentage thresholds, bucket transitions, or reference High crossovers.
- **Relational Persistence**: Uses SQLite for fast, robust local storage (never uses Excel as a database).

---

## 3. Project Directory Structure

```text
Stock Cycle Tracker/
├── run_app.py                 # Turnkey launcher with automated demo data seeding
├── requirements.txt           # Dependency requirements
├── pyproject.toml             # Package metadata and build configuration
├── sample_stocks.xlsx         # Sample Excel file for import testing
├── src/
│   └── stock_cycle_tracker/
│       ├── domain/            # Pure calculation engine, models, calendar & bucket rules
│       │   ├── models.py      # Typed dataclasses (Stock, Cycle, CycleAnalysis, etc.)
│       │   ├── buckets.py     # Deterministic bucket classifier
│       │   ├── calendar.py    # Indian equity trading calendar & holiday resolver
│       │   └── engine.py      # CycleEngine computing reference High & % changes
│       ├── providers/         # Market data providers & caching
│       │   ├── base.py        # MarketDataProvider abstract interface
│       │   ├── nse.py         # NSE provider adapter
│       │   ├── bse.py         # BSE provider adapter
│       │   ├── fallback.py    # Yahoo Finance adapter (.NS / .BO)
│       │   ├── composite.py   # Strict hierarchy orchestrator (NSE -> BSE -> Fallback)
│       │   ├── cached_provider.py # In-memory & SQLite cache
│       │   ├── session.py     # Market trading hours inspector (09:15-15:30 IST)
│       │   └── mock.py        # Hermetic mock provider for offline testing
│       ├── storage/           # SQLite database & repository
│       │   ├── db.py          # Relational schema management
│       │   └── repository.py  # Stock & Cycle CRUD repository
│       ├── services/          # Application services
│       │   ├── cycle_service.py # Orchestrates calculations and data feeds
│       │   ├── excel_service.py # OpenPyXL parser, validator & 18-col exporter
│       │   └── alert_service.py # Rule-based alert trigger engine
│       ├── ui/                # Rio Web UI
│       │   ├── app.py         # App shell and page routing
│       │   ├── state.py       # Service locator container
│       │   ├── theme.py       # Color palettes and badge styling
│       │   ├── components/    # Reusable components (Plotly chart, badges)
│       │   └── views/         # Dashboard, StockDetail, ManageCycles, Excel, Alerts
│       └── main.py            # CLI entry point and server runner
└── tests/                     # Comprehensive test suite (29 tests)
    ├── domain/                # Tests for buckets, calendar, and engine
    ├── providers/             # Tests for providers and caching
    ├── storage/               # Tests for SQLite repository
    ├── services/              # Tests for cycle, excel, and alert services
    └── test_e2e.py            # End-to-end tests verifying all 7 acceptance scenarios
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- `pip`

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Package in Editable Mode
```bash
pip install -e .
```

---

## 5. How to Run the Application

### Option A: Turnkey Web Launcher (Recommended)
Run the turnkey script to launch the Rio UI and automatically seed sample research cycles (RELIANCE, TCS, INFY, HDFCBANK) if the database is empty:
```bash
python run_app.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

Custom options:
```bash
python run_app.py --port 8080 --db my_stocks.db
```

---

### Option B: CLI Subcommands

#### 1. Calculate a Single Stock Cycle
```bash
python -m stock_cycle_tracker.main calculate --stock RELIANCE --date 2014-01-10
```
Output:
```text
============================================================
Stock:                  RELIANCE (Reliance Industries Limited)
Cycle:                  Cycle 1
Original Research Date: 10-Jan-2014
Recurring Date:         10-Jan
Actual Trading Date:    12-Jan-2026
Exchange:               NSE
Reference High:         INR 1,478.46
Current Price:          INR 1,310.00 (CLOSE)
Percentage Change:      -11.39%
Bucket:                 Downside 10–15%
Cycle Boundaries:       10-Jan-2026 -> 09-Jan-2027
============================================================
```

#### 2. Bulk Import from Excel
```bash
python -m stock_cycle_tracker.main import-excel --file sample_stocks.xlsx
```

#### 3. Export Full Calculated Analysis to Excel
```bash
python -m stock_cycle_tracker.main export-excel --output My_Stock_Cycle_Analysis.xlsx
```

#### 4. Launch the Web UI via Package Runner
```bash
python -m stock_cycle_tracker.main run --port 8000
```

---

## 6. Excel Specification

### Upload Schema (`.xlsx`)
Input files require two columns:
| Stock Name | Reference Date |
| :--- | :--- |
| `RELIANCE` | `10-Jan-2014` |
| `TCS` | `30-Jan-2016` |
| `INFY` | `2019-07-15` |

*Accepted date formats: `DD-Mon-YYYY`, `YYYY-MM-DD`, `DD/MM/YYYY`, and standard Excel date serials.*

### Export Schema (Complete 18-Column Report)
The generated export contains:
1. `S.No.`
2. `Stock Name`
3. `Company Name`
4. `Cycle` (e.g. `Cycle 1`)
5. `Original Reference Date` (e.g. `10-Jan-2014`)
6. `Recurring Reference Date` (e.g. `10-Jan`)
7. `Actual Reference Trading Date` (e.g. `12-Jan-2026`)
8. `Exchange` (`NSE` / `BSE`)
9. `Reference High` (Formatted currency)
10. `Current Price` (Formatted currency)
11. `Price Type` (`LIVE` / `CLOSE`)
12. `Calculation Date`
13. `% Change` (Formatted percentage)
14. `Bucket` (e.g. `Downside 10–15%`)
15. `Cycle Start`
16. `Cycle End`
17. `Data Source`
18. `Last Data Refresh`

---

## 7. Running Tests

Run the full pytest suite:
```bash
pytest
```
Expected output: **29 passed in ~1.5s (100% pass rate)**.
