# DAX Measures

All measures live in the `price_snapshots` table of the Power BI model. The data comes from a Supabase (PostgreSQL) database that is refreshed every 15 minutes by a GitHub Actions job.

## Date table

```dax
DateTable = CALENDAR(MIN(price_snapshots[captured_at]), MAX(price_snapshots[captured_at]))
```

Calendar table covering the captured date range, used for time-based visuals.

## Measures

```dax
Avg Price = AVERAGE(price_snapshots[price_usd])
```
Average price across the selected coins and time range.

```dax
24h Change % = AVERAGE(price_snapshots[price_change_24h])
```
Average 24-hour percentage change.

```dax
Price Volatility = STDEV.P(price_snapshots[price_usd])
```
Standard deviation of price over the captured snapshots. The headline risk measure.

```dax
Volatility Rank = RANKX(ALL(price_snapshots[coin_id]), [Price Volatility], , DESC)
```
Ranks every coin from most to least volatile, ignoring other filters on the page.

```dax
Session High = MAX(price_snapshots[price_usd])
Session Low = MIN(price_snapshots[price_usd])
```
Highest and lowest price captured in the selected period.

```dax
Price Range = [Session High] - [Session Low]
```
Spread between high and low, a simple volatility proxy.

```dax
Distinct Coins = DISTINCTCOUNT(price_snapshots[coin_id])
```
Number of unique coins being tracked.