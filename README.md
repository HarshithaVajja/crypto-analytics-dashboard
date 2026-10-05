# Real-Time Crypto Market Analytics

**Live dashboard:** [Open the live Data Studio dashboard](https://datastudio.google.com/reporting/1998f382-15bc-432e-9244-995a9c4aa39e)

The data refreshes every 15 minutes. A scheduled job starts a GitHub Actions workflow, which collects prices from the CoinGecko API and saves them in a Supabase PostgreSQL database. The dashboard reads from that database.

An end-to-end analytics project. Live cryptocurrency market data is collected every 15 minutes by an automated job and stored in a cloud PostgreSQL database. It is shaped with SQL window-function views, shown in a Power BI report with custom DAX measures, and published as a live public dashboard in Data Studio.

## Architecture

```
CoinGecko public API (top 50 coins by market cap)
        |
        v
GitHub Actions workflow
  runs fetch_crypto.py --once
        |
        v
Supabase PostgreSQL (cloud database)
  price_snapshots, coins + SQL views
        |
        +--> Power BI report (DAX measures, 2 pages)
        |
        +--> Data Studio dashboard (public live link)
```

A free scheduler (cron-job.org) triggers the GitHub Actions workflow every 15 minutes. The workflow also has its own GitHub schedule as a backup.

## Tech stack

| Layer | Tool |
|---|---|
| Data source | CoinGecko public API |
| Collection | Python (requests, psycopg2) |
| Automation | GitHub Actions + cron-job.org trigger |
| Database | PostgreSQL on Supabase |
| Modelling | SQL views (window functions) |
| Reporting | Power BI (DAX) and Data Studio |

## How the pipeline works

1. `fetch_crypto.py` calls the CoinGecko API and gets the top 50 coins by market cap. If the API says "too many requests" (HTTP 429), it waits and tries again.
2. Each run saves one new row per coin in the `price_snapshots` table: price, market cap, 24-hour volume, 24-hour price change and the time it was captured. Coin names are kept in the `coins` table.
3. A GitHub Actions workflow (`.github/workflows/collect.yml`) runs the script with `--once`. Database login details are stored as GitHub Secrets and are never in the code.
4. The database now grows by about 50 rows every 15 minutes, with no laptop involved.

## SQL layer

The file `sql/views.sql` has three views:

| View | What it does | SQL idea |
|---|---|---|
| `latest_prices` | Newest price row for each coin | `DISTINCT ON` |
| `top_movers` | Ranks coins by 24-hour price change | `RANK()` window function |
| `price_momentum` | Compares each price with the one before it | `LAG()` window function |

## DAX measures

The Power BI report uses custom measures. The full code with explanations is in [`dax_measures.md`](dax_measures.md).

| Measure | Purpose |
|---|---|
| DateTable | Calendar table for time analysis |
| Avg Price | Average price in the current filter |
| 24h Change % | Average 24-hour price change |
| Price Volatility | Standard deviation of price (`STDEV.P`) |
| Volatility Rank | Ranks coins by volatility (`RANKX`) |
| Session High / Low | Highest and lowest price captured |
| Price Range | High minus low |
| Distinct Coins | Number of different coins tracked |

## Dashboards

### Power BI (2 pages)

The report file is `crypto_analytics.pbix`. It connects to Supabase PostgreSQL.

![Overview page](screenshots/overview.png)

![Movers and volatility page](screenshots/Movers%20%26%20Volatility.png)

### Data Studio (live, public)

The [live dashboard](https://datastudio.google.com/reporting/1998f382-15bc-432e-9244-995a9c4aa39e) has two pages:

- **Price trend:** pick a coin from the drop-down to see its price line and average price.
- **Top movers:** bar chart of the coins with the biggest 24-hour price change.

It reads from the same Supabase database and refreshes every 15 minutes.

## Run it yourself

1. Create a free PostgreSQL database (for example on Supabase) and run the table setup and `sql/views.sql`.
2. Install the packages:

```
pip install -r requirements.txt
```

3. Set the database details as environment variables:

```
PGHOST=your-host
PGPORT=5432
PGDATABASE=postgres
PGUSER=your-user
PGPASSWORD=your-password
```

4. Collect one batch of prices:

```
python fetch_crypto.py --once
```

5. To automate it, add the same five values as GitHub Secrets (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`). The workflow in `.github/workflows/collect.yml` will use them.

## Repository structure

```
.
├── fetch_crypto.py              # collects prices from CoinGecko into PostgreSQL
├── migrate_to_cloud.py          # one-time move of earlier local data to the cloud database
├── requirements.txt             # Python packages
├── sql/
│   └── views.sql                # latest_prices, top_movers, price_momentum
├── dax_measures.md              # Power BI measures with explanations
├── crypto_analytics.pbix        # Power BI report
├── screenshots/                 # dashboard images used in this README
└── .github/workflows/
    └── collect.yml              # scheduled data collection
```

## What I would do next

- Send an alert (email or message) when a coin moves more than a set percentage.
- Add a drill-through page in Power BI with the full history of one coin.
- Add a data quality check that warns if a run saves fewer rows than expected.
- Package the collector in Docker so it runs the same way anywhere.