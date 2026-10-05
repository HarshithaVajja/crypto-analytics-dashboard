import argparse
import time
from datetime import datetime, timezone

import psycopg2
import requests
from psycopg2.extras import execute_values

API_URL = "https://api.coingecko.com/api/v3/coins/markets"


def get_conn():
    # Reads PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD from the environment
    return psycopg2.connect()


def fetch_market_data(retries=4):
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "price_change_percentage": "24h",
    }
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            if response.status_code == 429:
                wait = 30 * attempt
                print(f"Rate limited. Waiting {wait}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            wait = 10 * attempt
            print(f"Request failed: {e}. Retrying in {wait}s (attempt {attempt}/{retries})")
            time.sleep(wait)
    raise RuntimeError("CoinGecko API not reachable after retries")


def setup_database():
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS coins (
                    coin_id TEXT PRIMARY KEY,
                    symbol  TEXT,
                    name    TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS price_snapshots (
                    id               BIGSERIAL PRIMARY KEY,
                    coin_id          TEXT NOT NULL REFERENCES coins(coin_id),
                    price_usd        DOUBLE PRECISION,
                    market_cap       DOUBLE PRECISION,
                    total_volume     DOUBLE PRECISION,
                    price_change_24h DOUBLE PRECISION,
                    captured_at      TIMESTAMP NOT NULL
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_coin_time
                ON price_snapshots (coin_id, captured_at)
            """)
    finally:
        conn.close()


def save_to_db(data):
    captured_at = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC, one timestamp per batch
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            execute_values(
                cur,
                "INSERT INTO coins (coin_id, symbol, name) VALUES %s "
                "ON CONFLICT (coin_id) DO NOTHING",
                [(c["id"], c["symbol"], c["name"]) for c in data],
            )
            execute_values(
                cur,
                "INSERT INTO price_snapshots "
                "(coin_id, price_usd, market_cap, total_volume, price_change_24h, captured_at) "
                "VALUES %s",
                [
                    (
                        c["id"],
                        c["current_price"],
                        c["market_cap"],
                        c["total_volume"],
                        c["price_change_percentage_24h"],
                        captured_at,
                    )
                    for c in data
                ],
            )
    finally:
        conn.close()
    print(f"[{captured_at}] Saved {len(data)} coin snapshots.")


def job():
    save_to_db(fetch_market_data())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true",
                        help="fetch one snapshot and exit (used by automation)")
    args = parser.parse_args()

    setup_database()

    if args.once:
        job()
    else:
        import schedule

        def safe_job():
            try:
                job()
            except Exception as e:
                print(f"Run failed, will try again next cycle: {e}")

        schedule.every(15).minutes.do(safe_job)
        print("Starting scheduler... press Ctrl+C to stop.")
        safe_job()
        while True:
            schedule.run_pending()
            time.sleep(1)