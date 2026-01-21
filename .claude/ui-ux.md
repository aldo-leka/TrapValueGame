# UI/UX Specification: Components, Interactions & Visual Design

This document details the user interface components, state management, animations, and visual design system for Trap Or Value.

---

## Table of Contents
1. [Design System](#design-system)
2. [Page Structure](#page-structure)
3. [Component Specifications](#component-specifications)
4. [State Management](#state-management)
5. [Animations & Transitions](#animations--transitions)
6. [Responsive Design](#responsive-design)
7. [Accessibility](#accessibility)

---

## Design System

### Color Palette (Dark Mode)

```css
:root {
  /* Background Layers */
  --bg-primary: #0D1117;        /* Main background */
  --bg-secondary: #161B22;      /* Cards, panels */
  --bg-tertiary: #21262D;       /* Elevated elements */
  --bg-hover: #30363D;          /* Hover states */

  /* Text */
  --text-primary: #E6EDF3;      /* Primary text */
  --text-secondary: #8B949E;    /* Secondary/muted text */
  --text-muted: #484F58;        /* Disabled, hints */

  /* Semantic Colors */
  --positive: #3FB950;          /* Profits, gains, VALUE */
  --negative: #F85149;          /* Losses, TRAP */
  --warning: #D29922;           /* Caution, neutral */
  --info: #58A6FF;              /* Links, info */

  /* Financial Table Specific */
  --table-border: #30363D;
  --table-header-bg: #161B22;
  --table-row-alt: #0D1117;
  --table-highlight: rgba(88, 166, 255, 0.1);

  /* Gradients */
  --gradient-value: linear-gradient(135deg, #238636 0%, #3FB950 100%);
  --gradient-trap: linear-gradient(135deg, #DA3633 0%, #F85149 100%);
}
```

### Typography

```css
/* Font Stack */
--font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Scale */
--text-xs: 0.75rem;     /* 12px - table cells */
--text-sm: 0.875rem;    /* 14px - secondary */
--text-base: 1rem;      /* 16px - body */
--text-lg: 1.125rem;    /* 18px - emphasis */
--text-xl: 1.25rem;     /* 20px - headings */
--text-2xl: 1.5rem;     /* 24px - page titles */
--text-3xl: 2rem;       /* 32px - hero numbers */
```

### Spacing System

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
```

---

## Page Structure

### Game Flow States

```
┌─────────────────────────────────────────────────────────────┐
│                        GAME PAGE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  State: LOADING                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Skeleton loaders                        │   │
│  │              "Finding your next case..."             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  State: ANALYZING                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐  ┌─────────────────────────┐   │   │
│  │  │  Company Card   │  │   Financial Table       │   │   │
│  │  │  "Retailer X"   │  │   5 years of data       │   │   │
│  │  │  Sector badge   │  │   TIKR-style grid       │   │   │
│  │  └─────────────────┘  └─────────────────────────┘   │   │
│  │                                                      │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │            Narrative Panel                     │  │   │
│  │  │  "It is January 2018. This retailer..."       │  │   │
│  │  │  (typewriter effect)                          │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │         SWIPE CARD / BUTTONS                   │  │   │
│  │  │    ← TRAP            VALUE →                   │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  State: REVEALING                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Brief animation showing choice                      │   │
│  │  "Checking the markets..."                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  State: RESULT                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐  ┌─────────────────────────┐   │   │
│  │  │  Real Company   │  │   Price Chart           │   │   │
│  │  │  "GameStop"     │  │   24-month line chart   │   │   │
│  │  │  GME            │  │   T-0 → T+24mo         │   │   │
│  │  └─────────────────┘  └─────────────────────────┘   │   │
│  │                                                      │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │   RESULT: YOU WERE RIGHT! / TRAPPED!          │  │   │
│  │  │   Return: -77.3%                              │  │   │
│  │  │   [Play Again]  [Share]                       │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Company Card (`CompanyCard.razor`)

**Purpose:** Display obfuscated company identity during analysis phase.

```razor
@* Props *@
@code {
    [Parameter] public string FakeName { get; set; }       // "Retailer X"
    [Parameter] public string Sector { get; set; }         // "Consumer Discretionary"
    [Parameter] public string SnapshotDate { get; set; }   // "Jan 2018"
    [Parameter] public int YearsOfData { get; set; }       // 5
}
```

**Visual Structure:**
```
┌──────────────────────────────────────┐
│  🏪  RETAILER X                      │
│                                      │
│  ┌──────────────┐  ┌──────────────┐  │
│  │ Consumer     │  │ Jan 2018     │  │
│  │ Discretionary│  │ Snapshot     │  │
│  └──────────────┘  └──────────────┘  │
│                                      │
│  5 years of financial data           │
└──────────────────────────────────────┘
```

**Sector Icons:**
| Sector | Icon |
|--------|------|
| Technology | 💻 |
| Healthcare | 🏥 |
| Consumer Discretionary | 🏪 |
| Financials | 🏦 |
| Energy | ⚡ |
| Industrials | 🏭 |
| Materials | ⛏️ |
| Utilities | 💡 |
| Real Estate | 🏠 |
| Communication Services | 📡 |
| Consumer Staples | 🛒 |

---

### 2. Financial Table (`FinancialTable.razor`)

**Purpose:** Display 5 years of financial data in TIKR/Bloomberg style.

```razor
@code {
    [Parameter] public List<FinancialYear> Data { get; set; }
    [Parameter] public bool ShowTrends { get; set; } = true;

    public class FinancialYear {
        public int Year { get; set; }
        public decimal? Revenue { get; set; }
        public decimal? GrossMargin { get; set; }
        public decimal? OperatingIncome { get; set; }
        public decimal? EBITDA { get; set; }
        public decimal? NetIncome { get; set; }
        public decimal? FreeCashFlow { get; set; }
        public decimal? TotalDebt { get; set; }
        public decimal? Cash { get; set; }
        public decimal? SharesOutstanding { get; set; }

        // YoY changes (nullable)
        public decimal? RevenueYoY { get; set; }
        public decimal? NetIncomeYoY { get; set; }
    }
}
```

**Visual Structure:**
```
┌────────────────────────────────────────────────────────────────┐
│ FINANCIALS (USD Millions)                                      │
├──────────────┬─────────┬─────────┬─────────┬─────────┬─────────┤
│              │  2013   │  2014   │  2015   │  2016   │  2017   │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Revenue      │ 9,039.5 │ 9,296.0 │ 9,363.8 │ 8,607.9 │ 7,965.0 │
│              │         │   ↑2.8% │   ↑0.7% │  ↓8.1%  │  ↓7.5%  │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Gross Margin │  27.3%  │  28.1%  │  30.4%  │  32.5%  │  31.2%  │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ EBITDA       │   623.4 │   515.2 │   556.7 │  (89.4) │  (12.8) │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Net Income   │   354.2 │   (52.8)│  (156.3)│ (673.0) │  (105.4)│
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Free Cash    │   201.0 │   (35.2)│   123.5 │  (512.2)│   (75.8)│
│ Flow         │         │         │         │         │         │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Total Debt   │   350.0 │   350.0 │   350.0 │   815.0 │   815.0 │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Cash         │   573.5 │   564.2 │   538.3 │   512.9 │   604.5 │
├──────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Shares (M)   │   106.5 │   104.2 │   101.8 │   102.3 │   101.0 │
└──────────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

**Formatting Rules:**

| Condition | Format | Color |
|-----------|--------|-------|
| Positive value | `$1,234.5` | `--text-primary` |
| Negative value | `(1,234.5)` | `--negative` |
| Margin/Percentage | `32.5%` | `--text-primary` |
| Negative margin | `(12.5%)` | `--negative` |
| YoY positive | `↑2.8%` | `--positive` |
| YoY negative | `↓8.1%` | `--negative` |
| N/A | `—` | `--text-muted` |

**Row Highlight Logic:**
- Hover: `background: var(--bg-hover)`
- Net Income row with multiple negatives: Subtle red background tint
- FCF row with multiple negatives: Subtle red background tint

---

### 3. Narrative Panel (`NarrativePanel.razor`)

**Purpose:** Display AI-generated historical context with typewriter effect.

```razor
@code {
    [Parameter] public string Narrative { get; set; }
    [Parameter] public int TypeSpeed { get; set; } = 30;  // ms per char
    [Parameter] public EventCallback OnComplete { get; set; }

    private string _displayedText = "";
    private bool _isTyping = true;
    private bool _skipped = false;

    public async Task Skip() {
        _skipped = true;
        _displayedText = Narrative;
        _isTyping = false;
        await OnComplete.InvokeAsync();
    }
}
```

**Visual Structure:**
```
┌──────────────────────────────────────────────────────────────┐
│  📜 MARKET SNAPSHOT                                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  It is January 2018. This specialty retailer has been        │
│  struggling with the shift to digital commerce. Over the     │
│  past five years, revenue has declined from $9 billion to    │
│  just under $8 billion. The company has cycled through       │
│  multiple CEOs and strategic pivots.                         │
│                                                              │
│  Bulls argue: Strong brand recognition, loyal customer       │
│  base, significant cost-cutting potential.                   │
│                                                              │
│  Bears argue: Secular decline in physical retail,            │
│  competition from digital storefronts, mounting losses.█     │
│                                                              │
│                                    [Skip →]                  │
└──────────────────────────────────────────────────────────────┘
```

**Typewriter Implementation:**
```javascript
// In wwwroot/js/typewriter.js
export function typeText(elementId, text, speedMs, onComplete) {
    const element = document.getElementById(elementId);
    let index = 0;

    const cursor = document.createElement('span');
    cursor.className = 'typing-cursor';
    cursor.textContent = '█';

    function type() {
        if (index < text.length) {
            element.textContent = text.substring(0, index + 1);
            element.appendChild(cursor);
            index++;
            setTimeout(type, speedMs);
        } else {
            cursor.remove();
            onComplete();
        }
    }

    type();
}
```

---

### 4. Swipe Card (`SwipeCard.razor`)

**Purpose:** Capture user's VALUE/TRAP decision via swipe or button.

```razor
@code {
    [Parameter] public EventCallback<string> OnDecision { get; set; }
    [Parameter] public bool IsEnabled { get; set; } = true;

    private double _dragX = 0;
    private double _dragStartX = 0;
    private bool _isDragging = false;
    private string _overlayClass = "";

    private const double SWIPE_THRESHOLD = 100;  // pixels
    private const double PEEK_THRESHOLD = 30;    // pixels to show overlay

    private async Task HandleDragEnd() {
        if (_dragX > SWIPE_THRESHOLD) {
            await OnDecision.InvokeAsync("value");
        } else if (_dragX < -SWIPE_THRESHOLD) {
            await OnDecision.InvokeAsync("trap");
        }
        _dragX = 0;
        _isDragging = false;
    }
}
```

**Visual Structure:**
```
                    Normal State
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                      ┌─────────────┐                         │
│                      │             │                         │
│                      │   DECIDE    │                         │
│                      │             │                         │
│                      │  ← Swipe →  │                         │
│                      │             │                         │
│                      └─────────────┘                         │
│                                                              │
│       [🚫 TRAP]                            [✓ VALUE]        │
│                                                              │
└──────────────────────────────────────────────────────────────┘

               Swiping Right (VALUE)
┌──────────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░                                       │
│ ░░░░░░ VALUE ░░░░░░░░░░   ┌─────────────┐                    │
│ ░░░░░░░░░░░░░░░░░░░░░░       │             │                 │
│ ░░░░░░░ ✓ ░░░░░░░░░░░░       │   DECIDE    │→→→              │
│ ░░░░░░░░░░░░░░░░░░░░░░       │             │                 │
│ ░░░░░░░░░░░░░░░░░░░░░░       └─────────────┘                 │
│ ░░░░░░░░░░░░░░░░░░░░░░                                       │
└──────────────────────────────────────────────────────────────┘
  Green overlay reveals                Card dragged right
```

**Mobile Touch Support:**
```javascript
// Touch event handling
element.addEventListener('touchstart', (e) => {
    dragStartX = e.touches[0].clientX;
    isDragging = true;
});

element.addEventListener('touchmove', (e) => {
    if (!isDragging) return;
    const currentX = e.touches[0].clientX;
    dragX = currentX - dragStartX;
    updateCardPosition(dragX);
    updateOverlay(dragX);
});

element.addEventListener('touchend', handleDragEnd);
```

---

### 5. Result View (`ResultView.razor`)

**Purpose:** Reveal actual company and outcome after decision.

```razor
@code {
    [Parameter] public RevealData Data { get; set; }

    public class RevealData {
        public string Ticker { get; set; }
        public string CompanyName { get; set; }
        public string SnapshotDate { get; set; }
        public decimal PriceAtSnapshot { get; set; }
        public decimal PriceAt24Mo { get; set; }
        public decimal Return24Mo { get; set; }
        public string OutcomeLabel { get; set; }  // "value", "trap", "neutral"
        public string PlayerChoice { get; set; }
        public bool IsCorrect { get; set; }
        public List<PricePoint> PriceSeries { get; set; }
    }
}
```

**Visual Structure - Correct Guess:**
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│            🎯 YOU CALLED IT!                                │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │  GME                                                │    │
│   │  GameStop Corp.                                     │    │
│   │                                                     │    │
│   │  You said: TRAP ✓                                   │    │
│   │  Actual: TRAP                                       │    │
│   │                                                     │    │
│   │  2-Year Return: -77.3%                              │    │
│   │  $18.50 → $4.20                                     │    │
│   └────────────────────────────────────────────────────┘    │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │     $20 ─┐                                          │    │
│   │          └──┐                                       │    │
│   │     $15     └───┐                                   │    │
│   │                 └────┐                              │    │
│   │     $10              └────────┐                     │    │
│   │                               └───────┐             │    │
│   │     $5                                └─────        │    │
│   │     ├────────┬────────┬────────┬────────┤          │    │
│   │   Jan'18  Jul'18  Jan'19  Jul'19  Jan'20           │    │
│   └────────────────────────────────────────────────────┘    │
│                                                              │
│         [🔄 Play Again]          [📤 Share]                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Visual Structure - Wrong Guess:**
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│            😬 TRAPPED!                                      │
│                                                              │
│   You thought NVDA was a trap...                            │
│   It returned +342% over 2 years.                           │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │  NVDA                                               │    │
│   │  NVIDIA Corporation                                 │    │
│   │                                                     │    │
│   │  You said: TRAP ✗                                   │    │
│   │  Actual: VALUE                                      │    │
│   └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### 6. Price Chart (`PriceChart.razor`)

**Purpose:** Animated line chart showing 24-month price action.

```razor
@code {
    [Parameter] public List<PricePoint> Data { get; set; }
    [Parameter] public decimal StartPrice { get; set; }
    [Parameter] public decimal EndPrice { get; set; }
    [Parameter] public bool Animate { get; set; } = true;

    public class PricePoint {
        public DateTime Date { get; set; }
        public decimal Price { get; set; }
    }
}
```

**Chart Configuration (using Chart.js via MudBlazor or Blazor interop):**
```javascript
const config = {
    type: 'line',
    data: {
        datasets: [{
            data: pricePoints,
            borderColor: return > 0 ? '#3FB950' : '#F85149',
            borderWidth: 2,
            pointRadius: 0,
            fill: {
                target: 'origin',
                above: 'rgba(63, 185, 80, 0.1)',
                below: 'rgba(248, 81, 73, 0.1)'
            }
        }]
    },
    options: {
        animation: {
            duration: 2000,
            easing: 'easeOutQuart'
        },
        scales: {
            x: {
                type: 'time',
                grid: { color: '#30363D' }
            },
            y: {
                grid: { color: '#30363D' },
                ticks: {
                    callback: (value) => '$' + value.toFixed(0)
                }
            }
        },
        plugins: {
            annotation: {
                annotations: {
                    startLine: {
                        type: 'line',
                        yMin: startPrice,
                        yMax: startPrice,
                        borderColor: '#8B949E',
                        borderDash: [5, 5]
                    }
                }
            }
        }
    }
};
```

---

## State Management

### Game State Machine

```csharp
public enum GameState {
    Loading,      // Fetching next snapshot
    Analyzing,    // Player reviewing data
    Revealing,    // Brief transition after decision
    Result        // Showing outcome
}

public class GameStateService {
    public GameState CurrentState { get; private set; }
    public SnapshotData? CurrentSnapshot { get; private set; }
    public RevealData? CurrentReveal { get; private set; }
    public string? PlayerChoice { get; private set; }

    public event Action? OnStateChanged;

    public async Task LoadNextSnapshot() {
        CurrentState = GameState.Loading;
        NotifyStateChanged();

        CurrentSnapshot = await _gameApi.GetNextSnapshot();
        CurrentReveal = null;
        PlayerChoice = null;

        CurrentState = GameState.Analyzing;
        NotifyStateChanged();
    }

    public async Task MakeDecision(string choice) {
        PlayerChoice = choice;
        CurrentState = GameState.Revealing;
        NotifyStateChanged();

        // Brief delay for animation
        await Task.Delay(800);

        CurrentReveal = await _gameApi.RevealOutcome(
            CurrentSnapshot!.SnapshotId,
            choice
        );

        CurrentState = GameState.Result;
        NotifyStateChanged();
    }

    public async Task PlayAgain() {
        await LoadNextSnapshot();
    }

    private void NotifyStateChanged() => OnStateChanged?.Invoke();
}
```

### Session Statistics

```csharp
public class SessionStats {
    public int GamesPlayed { get; set; }
    public int CorrectGuesses { get; set; }
    public int ValuesCalled { get; set; }
    public int TrapsCalled { get; set; }
    public int ValuesCorrect { get; set; }
    public int TrapsCorrect { get; set; }

    public double Accuracy =>
        GamesPlayed > 0 ? (double)CorrectGuesses / GamesPlayed : 0;

    public double ValueAccuracy =>
        ValuesCalled > 0 ? (double)ValuesCorrect / ValuesCalled : 0;

    public double TrapAccuracy =>
        TrapsCalled > 0 ? (double)TrapsCorrect / TrapsCalled : 0;
}
```

---

## Animations & Transitions

### 1. Page Transitions

```css
/* Fade transition between states */
.game-state-enter {
    opacity: 0;
    transform: translateY(10px);
}

.game-state-enter-active {
    opacity: 1;
    transform: translateY(0);
    transition: opacity 300ms ease, transform 300ms ease;
}

.game-state-exit {
    opacity: 1;
}

.game-state-exit-active {
    opacity: 0;
    transition: opacity 200ms ease;
}
```

### 2. Swipe Card Physics

```css
.swipe-card {
    transition: transform 0.1s ease-out;
    will-change: transform;
}

.swipe-card.released {
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Overlay reveal */
.swipe-overlay {
    opacity: 0;
    transition: opacity 0.15s ease;
}

.swipe-overlay.peeking {
    opacity: 0.3;
}

.swipe-overlay.full {
    opacity: 1;
}
```

### 3. Result Reveal Sequence

```csharp
// In ResultView.razor
protected override async Task OnAfterRenderAsync(bool firstRender) {
    if (firstRender && Data != null) {
        // Step 1: Show outcome text (0ms)
        _showOutcome = true;
        StateHasChanged();

        // Step 2: Reveal company name (500ms)
        await Task.Delay(500);
        _showCompany = true;
        StateHasChanged();

        // Step 3: Animate chart (1000ms)
        await Task.Delay(500);
        _showChart = true;
        StateHasChanged();

        // Step 4: Show stats and buttons (2500ms)
        await Task.Delay(1500);
        _showActions = true;
        StateHasChanged();
    }
}
```

### 4. Number Counter Animation

```javascript
// Animate return percentage counting up/down
export function animateNumber(elementId, start, end, duration, format) {
    const element = document.getElementById(elementId);
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * eased;

        element.textContent = format(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Usage: animateNumber('return-pct', 0, -77.3, 1500, (n) => n.toFixed(1) + '%');
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile first */
--bp-sm: 640px;   /* Small tablets */
--bp-md: 768px;   /* Tablets */
--bp-lg: 1024px;  /* Small laptops */
--bp-xl: 1280px;  /* Desktops */
```

### Mobile Layout Adjustments

```css
/* Financial table on mobile: horizontal scroll */
@media (max-width: 768px) {
    .financial-table-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    .financial-table {
        min-width: 600px;
    }

    /* Compact row labels */
    .financial-table .row-label {
        font-size: var(--text-xs);
        white-space: nowrap;
    }
}

/* Swipe card: full width on mobile */
@media (max-width: 640px) {
    .swipe-card {
        width: 100%;
        margin: 0;
    }

    /* Larger touch targets for buttons */
    .decision-button {
        min-height: 56px;
        font-size: var(--text-lg);
    }
}
```

### Touch vs. Mouse Interactions

```razor
@code {
    private bool _isTouchDevice = false;

    protected override async Task OnAfterRenderAsync(bool firstRender) {
        if (firstRender) {
            _isTouchDevice = await JS.InvokeAsync<bool>(
                "eval",
                "'ontouchstart' in window"
            );
            StateHasChanged();
        }
    }
}

@if (_isTouchDevice) {
    <SwipeCard OnDecision="HandleDecision" />
} else {
    <SwipeCard OnDecision="HandleDecision" />
    <div class="button-fallback">
        <MudButton OnClick="() => HandleDecision(\"trap\")">TRAP</MudButton>
        <MudButton OnClick="() => HandleDecision(\"value\")">VALUE</MudButton>
    </div>
}
```

---

## Accessibility

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `←` / `A` | Select TRAP |
| `→` / `D` | Select VALUE |
| `Enter` / `Space` | Confirm selection (when focused) |
| `Tab` | Navigate between elements |
| `Escape` | Cancel/reset swipe |

### Screen Reader Support

```razor
<div role="main" aria-label="Stock analysis game">
    <section aria-labelledby="company-heading">
        <h2 id="company-heading" class="visually-hidden">Company Information</h2>
        <CompanyCard ... />
    </section>

    <section aria-labelledby="financials-heading">
        <h2 id="financials-heading">Financial Data</h2>
        <FinancialTable ... aria-describedby="financials-desc" />
        <p id="financials-desc" class="visually-hidden">
            5 years of annual financial data including revenue, margins, and cash flow.
        </p>
    </section>

    <section aria-labelledby="decision-heading">
        <h2 id="decision-heading" class="visually-hidden">Make Your Decision</h2>
        <SwipeCard ... aria-label="Swipe or click to decide: left for trap, right for value" />
    </section>
</div>
```

### Color Contrast

All text meets WCAG AA standards:
- Primary text on background: 13.5:1
- Secondary text on background: 7.2:1
- Positive (green) on background: 5.8:1
- Negative (red) on background: 5.1:1

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }

    .typewriter-effect {
        /* Show full text immediately */
        animation: none;
    }
}
```