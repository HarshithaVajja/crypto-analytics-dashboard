import sqlite3

import psycopg2
from psycopg2.extras import execute_values

SQLITE_PATH = "crypto_analytics.db"

src = sqlite3.connect(SQLITE_PATH)
sc = src.cursor()

dst = psycopg2.connect()  # uses the PG* settings in this terminal
with dst, dst.cursor() as cur:
    # Prevents duplicates if this script is run again
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_snapshots_coin_time
        ON price_snapshots (coin_id, captured_at)
    """)

    cur.execute("SELECT COUNT(*) FROM price_snapshots")
    before = cur.fetchone()[0]

    coins = sc.execute("SELECT coin_id, symbol, name FROM coins").fetchall()
    execute_values(
        cur,
        "INSERT INTO coins (coin_id, symbol, name) VALUES %s ON CONFLICT (coin_id) DO NOTHING",
        coins,
    )

    rows = sc.execute(
        "SELECT coin_id, price_usd, market_cap, total_volume, price_change_24h, captured_at "
        "FROM price_snapshots ORDER BY captured_at"
    ).fetchall()
    execute_values(
        cur,
        "INSERT INTO price_snapshots "
        "(coin_id, price_usd, market_cap, total_volume, price_change_24h, captured_at) "
        "VALUES %s ON CONFLICT (coin_id, captured_at) DO NOTHING",
        rows,
        page_size=1000,
    )

    cur.execute("SELECT COUNT(*) FROM price_snapshots")
    after = cur.fetchone()[0]

print(f"Local rows read: {len(rows)}")
print(f"Cloud rows before: {before}, after: {after}, added: {after - before}")
dst.close()
src.close()