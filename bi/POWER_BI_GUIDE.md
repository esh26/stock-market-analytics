# Power BI build guide (about 1 hour)

**Data:** `data/processed/prices_enriched.csv` (daily prices + indicators), `ticker_summary.csv`, `correlation_long.csv`, `monthly_returns.csv`.

## 1. Load and model
1. Get Data → Text/CSV → load all four files (Transform: check `date` is Date, numbers are Decimal).
2. Model view: relate `Prices[ticker]` → `Summary[ticker]` (many-to-one) and `Prices[ticker]` → `MonthlyReturns[ticker]`.
3. Create a calendar table: `Calendar = CALENDAR(MIN(Prices[date]), MAX(Prices[date]))`, relate `Calendar[Date]` → `Prices[date]`.

## 2. DAX measures (paste into the Prices table)
```DAX
Latest Close = CALCULATE ( AVERAGE ( Prices[close] ), Prices[date] = MAX ( Prices[date] ) )

Period Return % =
VAR firstC = CALCULATE ( AVERAGE ( Prices[close] ), Prices[date] = MIN ( Prices[date] ) )
VAR lastC  = CALCULATE ( AVERAGE ( Prices[close] ), Prices[date] = MAX ( Prices[date] ) )
RETURN DIVIDE ( lastC - firstC, firstC )

Annualised Volatility = STDEV.S ( Prices[daily_return] ) * SQRT ( 252 )

Sharpe Ratio = DIVIDE ( AVERAGE ( Prices[daily_return] ) * 252 - 0.02, [Annualised Volatility] )

Max Drawdown = MIN ( Prices[drawdown] )

Latest RSI = CALCULATE ( AVERAGE ( Prices[rsi14] ), Prices[date] = MAX ( Prices[date] ) )

RSI Signal = IF ( [Latest RSI] > 70, "Overbought", IF ( [Latest RSI] < 30, "Oversold", "Neutral" ) )

Trend Signal =
VAR s20 = CALCULATE ( AVERAGE ( Prices[sma20] ), Prices[date] = MAX ( Prices[date] ) )
VAR s50 = CALCULATE ( AVERAGE ( Prices[sma50] ), Prices[date] = MAX ( Prices[date] ) )
RETURN IF ( s20 > s50, "Bullish", "Bearish" )

Growth of 100 =
VAR firstC = CALCULATE ( AVERAGE ( Prices[close] ), FILTER ( ALLSELECTED ( Prices[date] ), Prices[date] = MINX ( ALLSELECTED ( Prices[date] ), Prices[date] ) ) )
RETURN DIVIDE ( AVERAGE ( Prices[close] ), firstC ) * 100
```

## 3. Report page layout
- **Slicers:** ticker (dropdown), sector, date range (between).
- **Cards:** Latest Close, Period Return %, Annualised Volatility, Sharpe Ratio, Max Drawdown, RSI Signal, Trend Signal.
- **Line chart:** date vs `close`, `sma20`, `sma50`. **Column (secondary axis):** `volume`.
- **Line chart:** `Growth of 100` by ticker (compare stocks). **Area chart:** `drawdown`.
- **Scatter:** X = `ann_vol`, Y = `ann_return`, details = `ticker`, colour = `sector` (from Summary).
- **Matrix:** rows `ticker_a`, columns `ticker_b`, values `correlation` with conditional-format background colours (blue to red).
- **Bar:** `sma_strategy_return` vs `total_return` by ticker (clustered).
- Theme: dark navy background to match the web dashboard.

## 4. Publish
File → Export → PDF, and save screenshots into `bi/screenshots/`. Add them to the README. (Publish to web needs a work or school account.)
