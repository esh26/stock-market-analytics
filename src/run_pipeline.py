"""Pipeline: raw OHLCV -> validation -> indicators -> statistics -> SQL -> BI-ready exports -> dashboard.

Usage:  python src/run_pipeline.py
"""
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, REPORTS, DOCS = ROOT / "data/raw/prices_raw.csv", ROOT / "data/processed", ROOT / "reports", ROOT / "docs"
RF, ANN = 0.02, 252


def validate(df):
    log = {"raw_rows": len(df), "duplicates": int(df.duplicated(["date", "ticker"]).sum()),
           "null_cells": int(df.isna().sum().sum()), "non_positive_prices": int((df[["open", "high", "low", "close"]] <= 0).sum().sum()),
           "ohlc_inconsistent": int(((df["high"] < df[["open", "close"]].max(axis=1) - 0.011) | (df["low"] > df[["open", "close"]].min(axis=1) + 0.011)).sum())}
    df = df.drop_duplicates(["date", "ticker"]).dropna()
    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)].copy()
    df["date"] = pd.to_datetime(df["date"])
    log["clean_rows"] = len(df)
    return df.sort_values(["ticker", "date"]).reset_index(drop=True), log


def indicators(g):
    g = g.copy(); c = g["close"]
    g["daily_return"] = c.pct_change()
    g["sma20"], g["sma50"] = c.rolling(20).mean(), c.rolling(50).mean()
    d = c.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean(), (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    g["rsi14"] = 100 - 100 / (1 + up / dn)
    g["vol30"] = g["daily_return"].rolling(30).std() * np.sqrt(ANN)
    g["cum_return"] = c / c.iloc[0] - 1
    g["drawdown"] = c / c.cummax() - 1
    return g


def summarise(df):
    wide = df.pivot(index="date", columns="ticker", values="daily_return")
    mkt = wide.mean(axis=1)
    rows = []
    for t in wide.columns:
        g = df[df.ticker == t].set_index("date"); r = wide[t].dropna()
        ann_vol = r.std() * np.sqrt(ANN)
        slope, icpt, rv, pv, se = stats.linregress(mkt.loc[r.index], r)
        t_stat, p_mean = stats.ttest_1samp(r, 0)
        jb, p_jb = stats.jarque_bera(r)
        sig = (g["sma20"] > g["sma50"]).shift(1, fill_value=False).astype(float)
        strat = (g["daily_return"] * sig).dropna()
        rows.append({"ticker": t, "sector": g["sector"].iloc[0], "total_return": g["close"].iloc[-1] / g["close"].iloc[0] - 1,
                     "ann_return": (1 + r).prod() ** (ANN / len(r)) - 1, "ann_vol": ann_vol,
                     "sharpe": (r.mean() * ANN - RF) / ann_vol, "max_drawdown": g["drawdown"].min(),
                     "beta": slope, "alpha_ann": icpt * ANN, "corr_market": rv, "mean_ret_t_stat": t_stat, "mean_ret_p_value": p_mean,
                     "skew": stats.skew(r), "excess_kurtosis": stats.kurtosis(r), "jarque_bera_p": p_jb,
                     "sma_strategy_return": (1 + strat).prod() - 1, "sma_strategy_sharpe": (strat.mean() * ANN - RF) / (strat.std() * np.sqrt(ANN)),
                     "sma_trades": int(sig.diff().abs().sum())})
    return pd.DataFrame(rows), wide, mkt


def run_sql(df):
    d = df.copy(); d["date"] = d["date"].dt.strftime("%Y-%m-%d")
    with sqlite3.connect(OUT / "stocks.db") as con:
        d.to_sql("prices", con, if_exists="replace", index=False)
        for block in (ROOT / "sql/queries.sql").read_text().split("-- name:")[1:]:
            name, sql = block.strip().split("\n", 1)
            res = pd.read_sql_query(sql, con); res.to_csv(REPORTS / f"{name.strip()}.csv", index=False)
            print(f"  SQL {name.strip():<32} {len(res)} rows")


def build_dashboard(df, summ, mkt):
    tk = list(dict.fromkeys(df["ticker"]))
    dates = sorted(df["date"].dt.strftime("%Y-%m-%d").unique())
    t = {k: {"s": df[df.ticker == k]["sector"].iloc[0], "c": df[df.ticker == k]["close"].round(2).tolist(),
             "v": (df[df.ticker == k]["volume"] // 1000).tolist()} for k in tk}
    mk = (100 * (1 + mkt.fillna(0)).cumprod()).round(2).tolist()
    s = summ.round(4).to_dict("records")
    payload = {"dates": dates, "tickers": tk, "t": t, "mkt": mk, "summary": s}
    html = (ROOT / "dashboard/template.html").read_text().replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    (DOCS / "index.html").write_text(html)
    print(f"  dashboard -> docs/index.html ({len(html) / 1024:.0f} KB)")


def main():
    for d in (OUT, REPORTS, DOCS):
        d.mkdir(parents=True, exist_ok=True)
    print("1/5 validate"); df, log = validate(pd.read_csv(RAW)); (REPORTS / "validation_report.json").write_text(json.dumps(log, indent=2)); print("  ", log)
    print("2/5 indicators"); df = pd.concat([indicators(g) for _, g in df.groupby("ticker")], ignore_index=True)
    print("3/5 statistics"); summ, wide, mkt = summarise(df)
    summ.round(4).to_csv(OUT / "ticker_summary.csv", index=False)
    wide.corr().round(3).to_csv(REPORTS / "correlation_matrix.csv")
    corr = wide.corr().round(3); corr.index.name, corr.columns.name = "ticker_a", "ticker_b"
    corr.stack().rename("correlation").reset_index().to_csv(OUT / "correlation_long.csv", index=False)
    m = df.assign(month=df["date"].dt.strftime("%Y-%m")).groupby(["ticker", "sector", "month"])["close"].agg(["first", "last"])
    (m["last"] / m["first"] - 1).round(4).rename("month_return").reset_index().to_csv(OUT / "monthly_returns.csv", index=False)
    out = df.copy(); out["date"] = out["date"].dt.strftime("%Y-%m-%d"); out.round(4).to_csv(OUT / "prices_enriched.csv", index=False)
    print("4/5 SQL"); run_sql(df)
    print("5/5 dashboard"); build_dashboard(df, summ, mkt)
    print(summ[["ticker", "total_return", "ann_vol", "sharpe", "max_drawdown", "beta", "mean_ret_p_value", "sma_strategy_return"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
