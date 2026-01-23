# Trap Or Value

A financial guessing game where players analyze historical stock data at a "snapshot" moment in time, then decide if the stock was a **Value** opportunity or a **Trap**. The reveal shows what actually happened over the next 24 months.

## Screenshots

*Coming soon*

## Features

- **Historical Analysis** - View 5 years of real financial data (revenue, margins, FCF, debt) presented at a specific point in time
- **AI Narratives** - Gemini-powered analysis that respects point-in-time integrity (never spoils the future)
- **Swipe Mechanics** - Tinder-style swipe left (Trap) or right (Value) to make your guess
- **Real Outcomes** - See what actually happened with interactive price charts showing the 24-month forward return
- **500+ Stocks** - S&P 500 companies with multiple historical snapshots each

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | .NET 9 Blazor Server | Real-time UI, SignalR-based interactivity |
| **UI Components** | MudBlazor | Material Design, dark theme, charts |
| **Backend API** | Python 3.12+ / FastAPI | Stock data fetching, snapshot generation |
| **Data Source** | yfinance | Historical prices & financials |
| **Database** | SQLite (async) | Snapshot storage, game state |
| **AI Narratives** | Google Gemini | Period-accurate story generation |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BLAZOR SERVER (:5000)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Game.razor   │  │ FinancialTable│ │ SwipeCard             │ │
│  │ (State Machine)│ │ (5yr metrics)│  │ (Touch + Mouse)       │ │
│  └──────┬───────┘  └──────────────┘  └───────────────────────┘ │
│         │                                                       │
│  ┌──────▼───────────────────────────────────────────────────┐  │
│  │                   GameStateService                        │  │
│  │  Loading → Analyzing → Revealing → Result → (repeat)      │  │
│  └──────┬───────────────────────────────────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │ HTTP
┌─────────▼───────────────────────────────────────────────────────┐
│                      PYTHON FASTAPI (:8000)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ GET /game/next│  │POST /reveal  │  │ POST /admin/seed      │ │
│  │ (random snap) │  │ (outcome)    │  │ (populate DB)         │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────────┘ │
│         │                 │                                     │
│  ┌──────▼─────────────────▼─────────────────────────────────┐  │
│  │               yfinance + SQLite                           │  │
│  │  - Fetch financials, prices, company info                 │  │
│  │  - Generate snapshots with 24mo forward returns           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- (Optional) [.NET 9 SDK](https://dotnet.microsoft.com/download) for local development
- (Optional) [Python 3.12+](https://www.python.org/downloads/) for local development
- (Optional) [Gemini API Key](https://aistudio.google.com/apikey) for AI narratives

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/aldo-leka/TrapValueGame.git
cd TrapValueGame

# Start all services
docker-compose up --build

# App available at http://localhost:5000
# API available at http://localhost:8000
```

### Seed the Database

The game needs stock data to play. Seed with a few stocks or the full S&P 500:

```bash
# Seed a few test stocks (fast)
curl -X POST http://localhost:8000/admin/seed \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT", "NVDA", "META", "GME"]}'

# Or seed all S&P 500 companies (takes ~30 minutes due to rate limiting)
curl -X POST http://localhost:8000/admin/seed-sp500

# Check seeding progress
curl http://localhost:8000/admin/seed-progress

# Check database status
curl http://localhost:8000/admin/status
```

### Local Development (without Docker)

**Python API:**
```bash
cd scripts
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Blazor App:**
```bash
cd TrapValueGame
dotnet watch
```

## How to Play

1. **Analyze** - Review 5 years of financial data for an anonymous company
2. **Read** - (Optional) Enable AI narratives via Settings for market context
3. **Decide** - Swipe RIGHT for Value (stock goes up) or LEFT for Trap (stock goes down)
4. **Reveal** - See the real company name and what actually happened over 24 months

### Outcome Classification

| Outcome | 24-Month Return | Description |
|---------|-----------------|-------------|
| **Value** | ≥ +30% | The stock was undervalued |
| **Trap** | ≤ -20% | The stock was a value trap |
| *Neutral* | -20% to +30% | *Excluded from game* |

### Difficulty Levels

| Difficulty | Criteria | Description |
|------------|----------|-------------|
| Easy | \|Return\| ≥ 50% | Obvious winners/losers |
| Medium | 10% < \|Return\| < 50% | Requires analysis |
| Hard | \|Return\| ≤ 10% | Close calls |

## AI Narratives

The game supports AI-generated market analysis that respects **point-in-time integrity** - the AI writes as if it's living in the snapshot year, with no knowledge of what happens next.

To enable:
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Click the Settings icon in the app
3. Enter your API key (stored only in session memory, never persisted)

The AI generates 3 paragraphs:
- Current state of the company
- Bull case (optimist view)
- Bear case (pessimist view)

## API Reference

### Game Endpoints

#### `GET /game/next`
Get a random playable snapshot.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `difficulty` | string | Filter by "easy", "medium", or "hard" |
| `sector` | string | Filter by sector (e.g., "Technology") |
| `exclude_ids` | string | Comma-separated snapshot IDs to exclude |

**Response:**
```json
{
  "snapshot_id": 123,
  "fake_name": "Tech Delta Corp",
  "sector": "Technology",
  "industry": "Semiconductors",
  "snapshot_date": "2018-06-15",
  "snapshot_year": 2018,
  "financials": [
    {
      "fiscal_year": 2017,
      "revenue": 1234.5,
      "net_income": 123.4,
      "free_cash_flow": 100.0
    }
  ]
}
```

#### `POST /game/reveal/{snapshot_id}?player_choice=value`
Reveal the outcome for a snapshot.

**Response:**
```json
{
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "snapshot_date": "2018-06-15",
  "price_at_snapshot": 65.23,
  "price_at_24mo": 142.50,
  "return_24mo": 1.185,
  "outcome_label": "value",
  "player_choice": "value",
  "is_correct": true,
  "price_series": [
    {"date": "2018-06-15", "price": 65.23},
    {"date": "2018-06-18", "price": 66.10}
  ]
}
```

### Admin Endpoints

#### `POST /admin/seed`
Seed database with specific tickers.

```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "force_refresh": false
}
```

#### `POST /admin/seed-sp500`
Seed all S&P 500 companies (runs in background).

#### `GET /admin/status`
Get database statistics.

```json
{
  "stocks": 503,
  "snapshots": 12450,
  "playable_snapshots": 8230
}
```

#### `GET /admin/seed-progress`
Track long-running seed operations.

```json
{
  "status": "running",
  "total": 503,
  "processed": 125,
  "current_ticker": "IBM",
  "errors": []
}
```

## Project Structure

```
/TrapValueGame
├── /TrapValueGame/           # Blazor Server Application
│   ├── /Components/
│   │   ├── /Game/            # Game UI components
│   │   ├── /Layout/          # App layout, nav
│   │   ├── /Pages/           # Routable pages
│   │   └── /Dialogs/         # Modal dialogs
│   ├── /Services/            # Business logic
│   │   ├── GameService.cs    # API client
│   │   ├── GameStateService.cs # State machine
│   │   └── GeminiService.cs  # AI narratives
│   └── /Models/              # DTOs
├── /scripts/                 # Python FastAPI
│   ├── /api/                 # HTTP endpoints
│   ├── /services/            # Data processing
│   │   ├── extractor.py      # yfinance wrapper
│   │   ├── snapshot_generator.py # Outcome calculation
│   │   └── database.py       # SQLite schema
│   └── /models/              # Pydantic schemas
├── /shared/                  # Docker shared volume
│   └── stocks.db             # SQLite database
├── /.claude/                 # Project documentation
│   ├── implementation-roadmap.md
│   ├── data-pipeline.md
│   ├── ui-ux.md
│   └── stock-selection.md
└── docker-compose.yml
```

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Infrastructure | ✅ Complete | Docker, project scaffolding |
| Phase 2: Data Pipeline | ✅ Complete | yfinance extraction, SQLite schema |
| Phase 3: Core API | ✅ Complete | FastAPI endpoints, snapshot logic |
| Phase 4: Blazor Foundation | ✅ Complete | MudBlazor, routing, state management |
| Phase 5: Game UI | ✅ Complete | Financial table, swipe card, charts |
| Phase 6: AI Narratives | ✅ Complete | Gemini integration, point-in-time prompts |
| Phase 7: Polish | 🔄 In Progress | Animations, error handling, tests |
| Phase 8: Deployment | 🔄 In Progress | Production config, CI/CD |

## Development

### Running Tests

```bash
# Python tests
cd scripts
pytest

# .NET tests
cd TrapValueGame
dotnet test

# E2E tests (Playwright)
cd tests/TrapValueGame.E2E
npx playwright test
```

### Environment Variables

**Blazor App:**
```env
ASPNETCORE_ENVIRONMENT=Development
PythonApiUrl=http://localhost:8000
DatabasePath=/shared/stocks.db
```

**Python API:**
```env
DATABASE_PATH=/shared/stocks.db
CACHE_DIR=/shared/cache
ALLOWED_ORIGINS=http://localhost:5000
DISABLE_SEEDING=false
```

## Key Design Decisions

### Point-in-Time Integrity
The most important rule: **never show data from the future**.
- Financials filtered by `report_date <= snapshot_date`
- 90-day filing delay assumed (fiscal year end + 90 days)
- AI prompts explicitly constrained to snapshot year

### Split-Adjusted Prices
Always use `auto_adjust=True` in yfinance to prevent fake "price drops" from stock splits that would corrupt return calculations.

### User-Provided API Keys
Gemini API keys are stored only in Blazor circuit memory (never persisted). This means:
- Keys cleared on page refresh
- No server-side key storage
- Each user provides their own key

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read the documentation in `/.claude/` before making significant changes.

## License

This project is for educational purposes.

## Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for historical stock data
- [MudBlazor](https://mudblazor.com/) for the UI component library
- [Google Gemini](https://ai.google.dev/) for AI narrative generation