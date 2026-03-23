"""
update_world_oil_prices.py
==========================
Daily update script for Brent Crude oil prices (USD/barrel).

- Downloads daily OHLCV from Yahoo Finance ticker BZ=F (Brent Crude Futures)
- Resamples to monthly close price
- Appends new months not yet in brent_oil_prices.csv
- Seeds historical data from hardcoded baseline if CSV doesn't exist

Run manually:
    python update_world_oil_prices.py

Automated by GitHub Actions every weekday at 09:00 Vietnam time.

Output CSV columns:
    month   YYYY-MM
    price   USD per barrel (monthly close)
"""

import csv
import logging
import sys
from datetime import date, datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("world_oil")

OUTPUT_CSV = Path("brent_oil_prices.csv")
FIELDNAMES = ["month", "price"]

# ── Historical baseline (seeded from index.html hardcode) ─────────────────────
HISTORICAL_BRENT = [
    ("2018-01", 69.1), ("2018-02", 65.3), ("2018-03", 66.8), ("2018-04", 72.1),
    ("2018-05", 76.9), ("2018-06", 74.4), ("2018-07", 74.2), ("2018-08", 72.5),
    ("2018-09", 78.9), ("2018-10", 80.5), ("2018-11", 65.0), ("2018-12", 55.1),
    ("2019-01", 59.2), ("2019-02", 64.4), ("2019-03", 67.2), ("2019-04", 71.2),
    ("2019-05", 69.8), ("2019-06", 64.4), ("2019-07", 63.9), ("2019-08", 59.2),
    ("2019-09", 62.2), ("2019-10", 59.7), ("2019-11", 62.5), ("2019-12", 66.0),
    ("2020-01", 63.6), ("2020-02", 55.7), ("2020-03", 33.7), ("2020-04", 18.4),
    ("2020-05", 30.0), ("2020-06", 40.9), ("2020-07", 43.4), ("2020-08", 44.8),
    ("2020-09", 41.0), ("2020-10", 40.2), ("2020-11", 43.6), ("2020-12", 50.6),
    ("2021-01", 55.1), ("2021-02", 61.3), ("2021-03", 64.6), ("2021-04", 65.2),
    ("2021-05", 68.5), ("2021-06", 74.5), ("2021-07", 74.6), ("2021-08", 70.6),
    ("2021-09", 74.8), ("2021-10", 83.3), ("2021-11", 79.9), ("2021-12", 73.7),
    ("2022-01", 85.2), ("2022-02", 97.0), ("2022-03", 117.3), ("2022-04", 108.1),
    ("2022-05", 113.0), ("2022-06", 122.7), ("2022-07", 105.8), ("2022-08", 99.7),
    ("2022-09", 91.6), ("2022-10", 95.0), ("2022-11", 88.8), ("2022-12", 77.4),
    ("2023-01", 83.4), ("2023-02", 83.5), ("2023-03", 78.3), ("2023-04", 83.5),
    ("2023-05", 75.5), ("2023-06", 74.5), ("2023-07", 81.0), ("2023-08", 85.0),
    ("2023-09", 93.4), ("2023-10", 91.1), ("2023-11", 83.6), ("2023-12", 77.6),
    ("2024-01", 79.7), ("2024-02", 82.0), ("2024-03", 87.0), ("2024-04", 88.9),
    ("2024-05", 84.1), ("2024-06", 84.3), ("2024-07", 84.9), ("2024-08", 79.7),
    ("2024-09", 73.8), ("2024-10", 74.4), ("2024-11", 72.7), ("2024-12", 73.7),
    ("2025-01", 79.9), ("2025-02", 77.2), ("2025-03", 75.1), ("2025-04", 72.4),
    ("2025-05", 65.2), ("2025-06", 68.3), ("2025-07", 71.5), ("2025-08", 74.2),
    ("2025-09", 72.8), ("2025-10", 75.1), ("2025-11", 76.4), ("2025-12", 74.9),
    ("2026-01", 82.3), ("2026-02", 86.1), ("2026-03", 84.7),
]


def load_existing_months(path: Path) -> dict:
    """Return {month: price} for all rows already saved."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig") as f:
        return {row["month"]: float(row["price"]) for row in csv.DictReader(f)}


def fetch_brent_monthly() -> dict:
    """
    Download Brent Crude daily data from Yahoo Finance (BZ=F)
    and return {YYYY-MM: monthly_close_price}.
    """
    try:
        import yfinance as yf
        import pandas as pd

        log.info("Downloading BZ=F from Yahoo Finance…")
        df = yf.download("BZ=F", start="2018-01-01", progress=False, auto_adjust=True)
        if df.empty:
            log.warning("Yahoo Finance returned empty data.")
            return {}

        # Resample: take last close of each calendar month
        monthly = df["Close"].resample("ME").last().dropna()
        result = {}
        for ts, price in monthly.items():
            ym = ts.strftime("%Y-%m")
            result[ym] = round(float(price), 2)
        log.info("Fetched %d monthly Brent prices from Yahoo Finance.", len(result))
        return result

    except Exception as e:
        log.error("Failed to fetch from Yahoo Finance: %s", e)
        return {}


def save_csv(data: dict, path: Path):
    """Write sorted month→price dict to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(data.items())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for month, price in rows:
            writer.writerow({"month": month, "price": price})
    log.info("✅ Saved %d rows → %s", len(rows), path)


def main():
    today_ym = date.today().strftime("%Y-%m")

    # Load existing data
    existing = load_existing_months(OUTPUT_CSV)

    if not existing:
        log.info("No existing CSV. Seeding historical baseline (%d months).", len(HISTORICAL_BRENT))
        for month, price in HISTORICAL_BRENT:
            existing[month] = price

    # Fetch fresh data from Yahoo Finance
    live = fetch_brent_monthly()

    added = 0
    if live:
        for month, price in live.items():
            if month not in existing or month == today_ym:
                existing[month] = price
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
