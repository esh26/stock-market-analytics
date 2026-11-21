-- name: 01_return_ranking
WITH f AS (SELECT ticker,
  FIRST_VALUE(close) OVER (PARTITION BY ticker ORDER BY date) AS first_close,
  LAST_VALUE(close) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_close,
  ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date) AS rn FROM prices)
SELECT ticker, ROUND(first_close, 2) AS first_close, ROUND(last_close, 2) AS last_close,
       ROUND(100 * (last_close / first_close - 1), 1) AS total_return_pct,
       RANK() OVER (ORDER BY last_close / first_close DESC) AS return_rank
FROM f WHERE rn = 1 ORDER BY return_rank;

-- name: 02_sector_annual_performance
SELECT strftime('%Y', date) AS year, sector, ROUND(AVG(daily_return) * 252 * 100, 1) AS ann_return_pct,
       ROUND(AVG(daily_return * daily_return) * 252 * 100, 2) AS variance_proxy
FROM prices WHERE daily_return IS NOT NULL GROUP BY year, sector ORDER BY year, ann_return_pct DESC;

-- name: 03_recent_golden_crosses
WITH x AS (SELECT ticker, date, sma20, sma50, LAG(sma20) OVER w AS p20, LAG(sma50) OVER w AS p50
           FROM prices WINDOW w AS (PARTITION BY ticker ORDER BY date))
SELECT ticker, date, 'golden_cross' AS signal FROM x
WHERE p20 <= p50 AND sma20 > sma50 ORDER BY date DESC LIMIT 15;

-- name: 04_best_and_worst_day
WITH r AS (SELECT ticker, date, daily_return,
  ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY daily_return ASC) AS worst_rn,
  ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY daily_return DESC) AS best_rn
  FROM prices WHERE daily_return IS NOT NULL)
SELECT ticker, MAX(CASE WHEN worst_rn = 1 THEN date END) AS worst_day,
       ROUND(100 * MIN(CASE WHEN worst_rn = 1 THEN daily_return END), 2) AS worst_pct,
       MAX(CASE WHEN best_rn = 1 THEN date END) AS best_day,
       ROUND(100 * MAX(CASE WHEN best_rn = 1 THEN daily_return END), 2) AS best_pct
FROM r GROUP BY ticker ORDER BY ticker;

-- name: 05_volume_spikes
WITH v AS (SELECT ticker, date, volume,
  AVG(volume) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS avg20 FROM prices)
SELECT ticker, COUNT(*) AS spike_days FROM v WHERE avg20 IS NOT NULL AND volume > 1.5 * avg20 GROUP BY ticker ORDER BY spike_days DESC;

-- name: 06_seasonality_by_month
SELECT strftime('%m', date) AS month, ROUND(AVG(daily_return) * 21 * 100, 2) AS avg_monthly_return_pct, COUNT(*) AS observations
FROM prices WHERE daily_return IS NOT NULL GROUP BY month ORDER BY month;
