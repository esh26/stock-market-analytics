# Tableau build guide (about 1 hour, Tableau Public is free)

**Data:** connect to `data/processed/prices_enriched.csv`. Add `ticker_summary.csv` and `correlation_long.csv` as separate data sources (relate on `ticker`).

## 1. Calculated fields
```
Annualised Volatility   = STDEV([daily_return]) * SQRT(252)
Sharpe Ratio            = (AVG([daily_return]) * 252 - 0.02) / [Annualised Volatility]
Trend Signal            = IF [sma20] > [sma50] THEN "Bullish" ELSE "Bearish" END
RSI Signal              = IF [rsi14] > 70 THEN "Overbought" ELSEIF [rsi14] < 30 THEN "Oversold" ELSE "Neutral" END
Growth of 100 (table calc) = SUM([close]) / LOOKUP(SUM([close]), FIRST()) * 100
Return in Range         = (SUM([close]) / LOOKUP(SUM([close]), FIRST())) - 1
Max Drawdown            = MIN([drawdown])
```
For `Growth of 100`: Edit Table Calculation → Compute using **Date**.

## 2. Worksheets
1. **Price trend:** Date (continuous) on Columns; `close`, `sma20`, `sma50` as Measure Names/Values lines; Volume as bars on a dual axis. Filter: ticker (single value dropdown).
2. **RSI:** `rsi14` line with reference lines at 30 and 70.
3. **Drawdown:** `drawdown` area chart.
4. **Compare stocks:** `Growth of 100` by ticker (colour = ticker), ticker multi-select filter.
5. **Risk vs return:** scatter of `ann_vol` (X) vs `ann_return` (Y), label = ticker, colour = sector.
6. **Correlation heatmap:** `ticker_a` rows, `ticker_b` columns, colour = `correlation` (diverging palette, centre 0), label = correlation.
7. **Strategy vs buy and hold:** bars of `sma_strategy_return` and `total_return` by ticker.

## 3. Dashboard
Combine the sheets (Dashboard → Size: Automatic), add ticker and date-range filters applied to all sheets, add a dark background (Format → Dashboard shading).

## 4. Publish
File → Save to Tableau Public. Copy the public link into the README ("Tableau dashboard") and the resume.
