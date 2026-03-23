"""
update_world_gold_prices.py
============================
Daily update script for world gold prices (XAU/USD, USD/oz).

- Downloads daily spot gold from Yahoo Finance ticker GC=F (Gold Futures)
- Resamples to monthly close price
- Appends new months not yet in world_gold_prices.csv
- Seeds historical data from hardcoded baseline if CSV doesn't exist

Run manually:
    python update_world_gold_prices.py

Automated by GitHub Actions every weekday at 09:00 Vietnam time.

Output CSV columns:
    month   YYYY-MM
    close   USD per troy oz (monthly close)
"""

import csv
import logging
import sys
from datetime import date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("world_gold")

OUTPUT_CSV = Path("world_gold_prices.csv")
FIELDNAMES = ["month", "close"]

# ── Historical baseline (seeded from index.html hardcode) ─────────────────────
HISTORICAL_GOLD_WORLD = [
    ("2015-01", 1283.8), ("2015-02", 1211.6), ("2015-03", 1183.4), ("2015-04", 1184.5),
    ("2015-05", 1190.2), ("2015-06", 1172.4), ("2015-07", 1095.2), ("2015-08", 1134.6),
    ("2015-09", 1115.3), ("2015-10", 1142.2), ("2015-11", 1064.7), ("2015-12", 1061.5),
    ("2016-01", 1117.7), ("2016-02", 1238.9), ("2016-03", 1233.0), ("2016-04", 1293.0),
    ("2016-05", 1215.7), ("2016-06", 1321.9), ("2016-07", 1352.2), ("2016-08", 1308.9),
    ("2016-09", 1317.6), ("2016-10", 1276.7), ("2016-11", 1173.3), ("2016-12", 1150.9),
    ("2017-01", 1210.6), ("2017-02", 1248.9), ("2017-03", 1247.3), ("2017-04", 1268.2),
    ("2017-05", 1268.6), ("2017-06", 1241.4), ("2017-07", 1269.4), ("2017-08", 1320.6),
    ("2017-09", 1280.6), ("2017-10", 1271.3), ("2017-11", 1274.9), ("2017-12", 1303.3),
    ("2018-01", 1345.1), ("2018-02", 1318.2), ("2018-03", 1325.4), ("2018-04", 1315.9),
    ("2018-05", 1298.5), ("2018-06", 1252.6), ("2018-07", 1222.9), ("2018-08", 1199.5),
    ("2018-09", 1192.0), ("2018-10", 1215.4), ("2018-11", 1222.1), ("2018-12", 1282.6),
    ("2019-01", 1321.4), ("2019-02", 1312.5), ("2019-03", 1292.3), ("2019-04", 1283.5),
    ("2019-05", 1305.9), ("2019-06", 1411.1), ("2019-07", 1413.7), ("2019-08", 1523.7),
    ("2019-09", 1472.7), ("2019-10", 1513.2), ("2019-11", 1464.0), ("2019-12", 1517.3),
    ("2020-01", 1586.9), ("2020-02", 1577.4), ("2020-03", 1575.2), ("2020-04", 1686.9),
    ("2020-05", 1731.5), ("2020-06", 1781.0), ("2020-07", 1974.2), ("2020-08", 1967.8),
    ("2020-09", 1885.8), ("2020-10", 1878.4), ("2020-11", 1776.8), ("2020-12", 1898.7),
    ("2021-01", 1842.8), ("2021-02", 1727.5), ("2021-03", 1707.7), ("2021-04", 1767.9),
    ("2021-05", 1906.8), ("2021-06", 1770.2), ("2021-07", 1813.9), ("2021-08", 1813.5),
    ("2021-09", 1756.9), ("2021-10", 1782.8), ("2021-11", 1775.0), ("2021-12", 1829.5),
    ("2022-01", 1797.4), ("2022-02", 1908.8), ("2022-03", 1937.3), ("2022-04", 1896.4),
    ("2022-05", 1837.6), ("2022-06", 1807.2), ("2022-07", 1761.0), ("2022-08", 1711.1),
    ("2022-09", 1661.8), ("2022-10", 1632.8), ("2022-11", 1768.6), ("2022-12", 1823.5),
    ("2023-01", 1928.3), ("2023-02", 1826.8), ("2023-03", 1970.8), ("2023-04", 1989.3),
    ("2023-05", 1963.0), ("2023-06", 1920.2), ("2023-07", 1965.6), ("2023-08", 1940.1),
    ("2023-09", 1848.5), ("2023-10", 1984.7), ("2023-11", 2036.2), ("2023-12", 2063.2),
    ("2024-01", 2039.6), ("2024-02", 2044.2), ("2024-03", 2234.0), ("2024-04", 2285.9),
    ("2024-05", 2327.8), ("2024-06", 2325.2), ("2024-07", 2447.6), ("2024-08", 2502.5),
    ("2024-09", 2634.7), ("2024-10", 2746.2), ("2024-11", 2650.5), ("2024-12", 2624.6),
    ("2025-01", 2801.3), ("2025-02", 2854.9), ("2025-03", 3123.3), ("2025-04", 3288.4),
    ("2025-05", 3294.9), ("2025-06", 3303.1), ("2025-07", 3290.0), ("2025-08", 3452.4),
    ("2025-09", 3858.7), ("2025-10", 4002.8), ("2025-11", 4252.1), ("2025-12", 4318.6),
    ("2026-01", 4847.9), ("2026-02", 5263.8), ("2026-03", 4836.9),
]


def load_existing_months(path: Path) -> dict:
    """Return {month: close} for all rows already saved."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig") as f:
        return {row["month"]: float(row["close"]) for row in csv.DictReader(f)}


def fetch_gold_monthly() -> dict:
    """
    Download XAU/USD (Gold Futures GC=F) from Yahoo Finance
    and return {YYYY-MM: monthly_close_price}.
    """
    try:
        import yfinance as yf

        log.info("Downloading GC=F (Gold) from Yahoo Finance…")
        df = yf.download("GC=F", start="2015-01-01", progress=False, auto_adjust=True)
        if df.empty:
            log.warning("Yahoo Finance returned empty data for GC=F.")
            return {}

        # Flatten MultiIndex columns if present (yfinance >=0.2.x)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(c) for c in col).strip('_') for col in df.columns]
        close_col = next((c for c in df.columns if 'close' in c.lower() or c.lower() == 'close'), None)
        if close_col is None:
            log.warning("No 'Close' column found. Columns: %s", df.columns.tolist())
            return {}

        monthly = df[close_col].resample("ME").last().dropna()
        result = {}
        for ts, price in monthly.items():
            ym = pd.Timestamp(ts).strftime("%Y-%m")
            result[ym] = round(float(price), 2)
        log.info("Fetched %d monthly XAU/USD prices from Yahoo Finance.", len(result))
        return result

    except Exception as e:
        log.error("Failed to fetch from Yahoo Finance: %s", e)
        return {}


def save_csv(data: dict, path: Path):
    """Write sorted month→close dict to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(data.items())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for month, close in rows:
            writer.writerow({"month": month, "close": close})
    log.info("✅ Saved %d rows → %s", len(rows), path)


def main():
    today_ym = date.today().strftime("%Y-%m")

    # Load existing data
    existing = load_existing_months(OUTPUT_CSV)

    if not existing:
        log.info("No existing CSV. Seeding historical baseline (%d months).", len(HISTORICAL_GOLD_WORLD))
        for month, close in HISTORICAL_GOLD_WORLD:
            existing[month] = close

    # Fetch fresh data from Yahoo Finance
    live = fetch_gold_monthly()

    added = 0
    if live:
        for month, close in live.items():
            if month not in existing or month == today_ym:
                existing[month] = close
                added += 1
        log.info("Merged live data: %d month(s) new/updated.", added)
    else:
        log.warning("No live data fetched — using existing/baseline only.")

    if added == 0 and OUTPUT_CSV.exists():
        log.info("✅ No new months to add. Data is up-to-date.")
        sys.exit(0)

    save_csv(existing, OUTPUT_CSV)


if __name__ == "__main__":
    main()
