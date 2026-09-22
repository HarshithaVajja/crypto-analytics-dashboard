# Real-Time Crypto Market Analytics Dashboard

An end-to-end analytics pipeline that pulls live cryptocurrency market data from a public API, stores and models it in SQL, and visualizes it in Power BI with custom DAX measures for volatility, momentum, and ranking.

## Overview

This project tracks live prices, market caps, trading volume, and 24h price changes for 50 cryptocurrencies, refreshed on a schedule, and turns that raw data into an analyst-ready dashboard — top gainers/losers, price trend lines, and a volatility-vs-volume view.

**Stack:** Python (ingestion) → SQLite (storage & analytical views) → Power BI (data model, DAX, dashboard)

## Architecture

```
CoinGecko public API
        │
        ▼
Python ingestion script (fetch_crypto.py)
   - runs on a schedule
   - fetches price/volume/market cap for 50 coins
        │
        ▼
SQLite database (crypto_analytics.db)
   - raw price_snapshots table
   - analytical SQL views (latest_prices, top_movers, price_momentum)
        │
        ▼
Power BI (crypto_analytics.pbix)
   - data model with relationships
   - DAX measures (volatility, moving averages, ranking)
   - 2-page interactive dashboard
```

## Data pipeline (Python + SQL)

`fetch_crypto.py` calls the CoinGecko `/coins/markets` endpoint on a repeating schedule and writes each snapshot into SQLite. No API key required.

SQL views built on top of the raw data:

- **`latest_prices`** — each coin's most recent snapshot, using a self-join on `MAX(captured_at)`
- **`top_movers`** — coins ranked by 24h % change using `RANK() OVER (...)`
- **`price_momentum`** — price change between consecutive snapshots using `LAG() OVER (PARTITION BY coin_id ORDER BY captured_at)`

## DAX measures

| Measure | Formula | Purpose |
|---|---|---|
| Avg Price | `AVERAGE(price_snapshots[price_usd])` | Average price across tracked coins |
| 24h Change % | `AVERAGE(price_snapshots[price_change_24h])` | Average 24h % change |
| Price Volatility | `STDEV.P(price_snapshots[price_usd])` | Standard deviation of price — a volatility indicator |
| Volatility Rank | `RANKX(ALL(price_snapshots[coin_id]), [Price Volatility], , DESC)` | Ranks coins from most to least volatile |
| Session High / Low | `MAX(...)` / `MIN(...)` | Highest / lowest price captured |
| Price Range | `[Session High] - [Session Low]` | Spread between high and low |
| Distinct Coins | `DISTINCTCOUNT(price_snapshots[coin_id])` | Count of unique coins tracked |

## Dashboard

**Page 1 — Overview**
- KPI cards: average price, 24h change %, distinct coins tracked
- Ranked table of coins by market cap
- Price trend line filterable by coin (via slicer)

![Overview](screenshots/overview.png)

**Page 2 — Movers & Volatility**
- Top gainers/losers bar chart (24h % change)
- Volatility ranking table
- Volume vs. Volatility scatter chart — highlights coins with both high trading activity and high price swings (Bitcoin stood out clearly here despite being the most established coin in the set)

![Movers & Volatility](screenshots/Movers%20%26%20Volatility.png)

## What I'd do next

- Move from SQLite to PostgreSQL for native `STDDEV_POP()` support and better concurrent read/write handling
- Set up scheduled refresh via Power BI Service instead of manual refresh
- Add a third dashboard page with drill-through to a single coin's full detail view
- Containerize the ingestion script with Docker and deploy it to run continuously in the cloud rather than a local terminal

## Files in this repo

- `fetch_crypto.py` — ingestion script
- `crypto_analytics.db` — SQLite database with raw data and views
- `crypto_analytics.sqbpro` — DB Browser for SQLite project file
- `crypto_analytics.pbix` — Power BI dashboard file
- `screenshots/` — dashboard page screenshots
