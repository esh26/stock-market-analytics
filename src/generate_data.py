"""Generate simulated daily OHLCV data for 10 fictional stocks in 5 sectors (seeded, reproducible).

Prices follow a market + sector + stock-specific factor model with a high-volatility regime in 2022.
Replace data/raw/prices_raw.csv with real data (date,ticker,sector,open,high,low,close,volume) and the
rest of the pipeline works unchanged.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 7
SECTORS = {"Technology": ["NVTX", "QBYT", "CLDR"], "Financials": ["ARGB", "MRDN"], "Energy": ["SOLX", "PTRL"],
           "Healthcare": ["HLXA", "VRTA"], "Consumer": ["BRND", "FRSH"]}
# ticker: (market beta, annual drift, idiosyncratic annual vol, start price)
PARAMS = {"NVTX": (1.5, .22, .22, 120), "QBYT": (1.3, .14, .25, 85), "CLDR": (1.2, .10, .28, 60),
          "ARGB": (1.1, .08, .18, 150), "MRDN": (0.9, .05, .16, 95), "SOLX": (1.0, .16, .30, 45),
          "PTRL": (0.8, .04, .24, 70), "HLXA": (0.7, .09, .17, 210), "VRTA": (0.6, .06, .20, 55),
          "BRND": (0.8, .07, .15, 130), "FRSH": (0.9, .12, .22, 40)}


def generate(path: Path) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dates = pd.bdate_range("2021-01-04", "2026-11-19")
    T = len(dates)
    sig = np.where((dates >= "2022-01-03") & (dates <= "2022-10-31"), 0.016, 0.0078)
    mdrift = np.where((dates >= "2022-01-03") & (dates <= "2022-10-31"), -0.0006, 0.0005)
    mkt = mdrift + sig * rng.standard_normal(T)
    sec_f = {s: 0.005 * rng.standard_normal(T) for s in SECTORS}
    rows = []
    for sec, tickers in SECTORS.items():
        for tk in tickers:
            beta, mu, iv, p0 = PARAMS[tk]
            r = beta * mkt + sec_f[sec] + (mu / 252) + iv / np.sqrt(252) * rng.standard_normal(T)
            close = p0 * np.exp(np.cumsum(r))
            prev = np.r_[p0, close[:-1]]
            op = prev * (1 + 0.002 * rng.standard_normal(T))
            hi = np.maximum(op, close) * (1 + np.abs(0.004 * rng.standard_normal(T)))
            lo = np.minimum(op, close) * (1 - np.abs(0.004 * rng.standard_normal(T)))
            vol = (rng.lognormal(13.5, 0.3, T) * (1 + 25 * np.abs(r))).astype(int)
            rows.append(pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "ticker": tk, "sector": sec,
                                      "open": op.round(2), "high": hi.round(2), "low": lo.round(2),
                                      "close": close.round(2), "volume": vol}))
    df = pd.concat(rows, ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data/raw/prices_raw.csv"
    print(f"Wrote {len(generate(out)):,} rows -> {out}")
