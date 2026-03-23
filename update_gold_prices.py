"""
update_gold_prices.py
=====================
Daily wrapper for the SJC gold price crawler.

Called automatically by GitHub Actions every weekday at 09:00 Vietnam time.
Fetches today's SJC gold price (Hồ Chí Minh) and appends it to gold_prices.csv.

If today is a weekend or the date already exists in the CSV, the script exits
gracefully without making any changes.

Usage:
    python update_gold_prices.py
"""

import csv
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# ── Reuse crawler helpers ──────────────────────────────────────────────────────
from sjc_gold_crawler import scrape, load_existing_dates

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_CSV = Path("gold_prices.csv")
FIELDNAMES = ["date", "buy", "sell", "source"]
SOURCE_TAG = "sjc.com.vn"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("update_gold")


def last_weekday(today: date) -> date:
    """Return today if it's Mon–Fri, otherwise the most recent Friday."""
    if today.weekday() < 5:          # 0=Mon … 4=Fri
        return today
    days_back = today.weekday() - 4  # Sat→1, Sun→2
    return today - timedelta(days=days_back)


def main():
    target = last_weekday(date.today())
    log.info("Target date: %s (weekday=%d)", target, target.weekday())

    # Skip if already recorded
    existing = load_existing_dates(OUTPUT_CSV)
    if target.isoformat() in existing:
        log.info("✅ Date %s already in %s — nothing to do.", target, OUTPUT_CSV)
        sys.exit(0)

    # Scrape
    records = scrape(target, target)

    if not records:
        log.warning("⚠ No data returned for %s (holiday or no trading).", target)
        sys.exit(0)

    # Append to CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    file_exists = OUTPUT_CSV.exists()
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for row in records:
            writer.writerow({
                "date":   row["date"],
                "buy":    row["buy"],
                "sell":   row["sell"],
                "source": SOURCE_TAG,
            })

    log.info("✅ Appended %d row(s) to %s.", len(records), OUTPUT_CSV)


if __name__ == "__main__":
    main()
