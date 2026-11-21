# Stock Market Analytics: Risk, Indicators and Dashboards

[![Live Dashboard](https://img.shields.io/badge/Live-Dashboard-4d8dff?style=for-the-badge)](https://esh26.github.io/stock-market-analytics/)

End-to-end market analytics: **Python (Pandas, SciPy) → SQL (SQLite) → statistical testing → live web dashboard → Power BI and Tableau dashboards**. It answers: *which stocks gave the best risk-adjusted return, how are they related, and do simple technical signals add value?*

**Live dashboard:** https://esh26.github.io/stock-market-analytics/ *(enable GitHub Pages: Settings → Pages → Branch `main`, folder `/docs`)*

> **Data note:** prices are **simulated** (seeded generator in `src/generate_data.py`): 11 fictional stocks, 5 sectors, daily OHLCV from 2021-01-04 to 2026-11-19 (16,874 rows) with a market factor, sector factors and a high-volatility regime in 2022. Findings describe the simulation, not real markets, and nothing here is investment advice. Replace `data/raw/prices_raw.csv` with real data in the same columns and the pipeline runs unchanged.

## What it does
| Stage | What happens | Output |
|---|---|---|
| Validate (Pandas) | checks duplicates, nulls, non-positive prices, OHLC consistency | `reports/validation_report.json` |
| Indicators | daily return, SMA 20/50, RSI(14), 30-day volatility, cumulative return, drawdown | `data/processed/prices_enriched.csv` |
| Statistics (SciPy) | annualised return and volatility, Sharpe ratio, max drawdown, beta and alpha (regression vs equal-weight index), t-test on mean return, Jarque-Bera normality test, skew, kurtosis, correlation matrix, SMA-crossover backtest | `data/processed/ticker_summary.csv`, `reports/correlation_matrix.csv` |
| SQL | 6 queries: return ranking, sector performance by year, golden-cross signals (`LAG`), best/worst day (`ROW_NUMBER`), volume spikes (rolling window), month-of-year seasonality | `sql/queries.sql`, `reports/*.csv` |
| Live dashboard | stock and range selectors, price + SMA + volume, RSI, drawdown, multi-stock comparison, risk-return scatter, correlation heatmap, summary table, auto-insights, CSV export | `docs/index.html` |
| Power BI / Tableau | BI-ready tables plus DAX measures, calculated fields and build guides | `bi/` |

## Quick start
```bash
git clone https://github.com/esh26/stock-market-analytics && cd stock-market-analytics
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/generate_data.py      # optional: regenerate simulated prices
python src/run_pipeline.py       # validate -> indicators -> statistics -> SQL -> dashboard
python -m http.server -d docs 8000   # open http://localhost:8000
```

## Findings (on the simulated data)
- **NVTX** had the best risk-adjusted performance (Sharpe 1.13, +685% over the period) and the highest beta (1.47); **VRTA** had the lowest beta (0.65).
- Only **NVTX and SOLX** have a mean daily return statistically different from zero at the 5% level (t-test); for the other nine stocks, average returns are not distinguishable from noise.
- **CLDR** suffered the deepest drawdown (-73%); **PTRL** had the weakest total return (-43%).
- Correlations between stocks are positive but moderate (0.12 to 0.49, average 0.28), so diversification across sectors reduced risk.
- In the simulated 2022 high-volatility regime every sector fell; **Technology** fell most (about -23.6% annualised average daily return).
- The **SMA 20/50 crossover strategy beat buy-and-hold on 6 of 11 stocks**, mainly by avoiding long downtrends, but lagged on the strongest uptrends (NVTX, SOLX). No transaction costs were modelled.

## Power BI and Tableau
`bi/POWER_BI_GUIDE.md` and `bi/TABLEAU_GUIDE.md` contain the data model, DAX measures, Tableau calculated fields and a page layout. Once built, add screenshots to `bi/screenshots/` and the public Tableau link here:
- Tableau Public: *add link*
- Power BI screenshots: *add images*

## Project structure
```
├── data/raw/prices_raw.csv            # simulated OHLCV
├── data/processed/                    # enriched prices, summary, correlations, monthly returns (BI-ready)
├── sql/queries.sql                    # 6 analysis queries
├── src/generate_data.py               # reproducible data generator
├── src/run_pipeline.py                # full pipeline
├── dashboard/template.html            # dashboard source (data injected at build)
├── docs/index.html                    # built dashboard (GitHub Pages)
├── bi/                                # Power BI and Tableau guides, DAX, calculated fields
└── reports/                           # SQL outputs, validation report, correlation matrix
```

## Limitations
Simulated data; a single-factor market model; no transaction costs, slippage or out-of-sample testing; returns are assumed independent across days. Next steps: real market data, walk-forward backtesting, and a portfolio optimiser.

## Author
Sarvesh Saravanan · [LinkedIn](https://linkedin.com/in/sarveshsv) · [GitHub](https://github.com/esh26) · svsarvesh264@gmail.com
