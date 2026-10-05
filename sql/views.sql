-- Analytical views for the crypto analytics pipeline (PostgreSQL / Supabase)

-- 1. Latest snapshot per coin
CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (coin_id) *
FROM price_snapshots
ORDER BY coin_id, captured_at DESC;

-- 2. Coins ranked by 24h price change (window function: RANK)
CREATE OR REPLACE VIEW top_movers AS
SELECT
    c.name,
    lp.price_usd,
    lp.price_change_24h,
    RANK() OVER (ORDER BY lp.price_change_24h DESC) AS gain_rank
FROM latest_prices lp
JOIN coins c ON c.coin_id = lp.coin_id;

-- 3. Price change between consecutive snapshots (window function: LAG)
CREATE OR REPLACE VIEW price_momentum AS
SELECT
    coin_id,
    captured_at,
    price_usd,
    LAG(price_usd) OVER (PARTITION BY coin_id ORDER BY captured_at) AS previous_price,
    price_usd - LAG(price_usd) OVER (PARTITION BY coin_id ORDER BY captured_at) AS price_delta
FROM price_snapshots;