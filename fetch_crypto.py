import requests
import sqlite3
from datetime import datetime

DB_PATH = "crypto_analytics.db"
API_URL = "https://api.coingecko.com/api/v3/coins/markets"

def fetch_market_data():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "price_change_percentage": "24h"
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS coins (
            coin_id TEXT PRIMARY KEY,
            symbol TEXT,
            name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT,
            price_usd REAL,
            market_cap REAL,
            total_volume REAL,
            price_change_24h REAL,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for coin in data:
        cur.execute("""
            INSERT OR IGNORE INTO coins (coin_id, symbol, name)
            VALUES (?, ?, ?)
        """, (coin["id"], coin["symbol"], coin["name"]))
        cur.execute("""
            INSERT INTO price_snapshots
            (coin_id, price_usd, market_cap, total_volume, price_change_24h, captured_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            coin["id"],
            coin["current_price"],
            coin["market_cap"],
            coin["total_volume"],
            coin["price_change_percentage_24h"],
            datetime.utcnow()
        ))
    conn.commit()
    conn.close()
    print(f"[{datetime.utcnow()}] Saved {len(data)} coin snapshots.")

import schedule
import time

def job():
    data = fetch_market_data()
    save_to_db(data)

if __name__ == "__main__":
    setup_database()
    schedule.every(15).minutes.do(job)
    print("Starting scheduler... press Ctrl+C to stop.")
    job()  # run once immediately
    while True:
        schedule.run_pending()
        time.sleep(1)