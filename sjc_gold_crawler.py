"""
SJC Gold Price History Crawler
================================
Crawls daily gold prices (Hồ Chí Minh) from sjc.com.vn/bieu-do-gia-vang
using headless Chrome and saves to CSV.

Confirmed DOM structure (March 2026):
  - Date input : id="datesearch"  type="text"  format DD/MM/YYYY
  - Submit btn : class="button-datesearch"  text="Tra cứu"
  - Page stack : ASP.NET WebForms

Requirements:
    pip install selenium webdriver-manager beautifulsoup4

Usage:
    # Basic — crawl from a start date to today
    python sjc_gold_crawler.py --start 2025-01-01

    # Custom date range and output file
    python sjc_gold_crawler.py --start 2024-01-01 --end 2025-12-31 --output gold_2024.csv

    # Resume / append to existing CSV (skips dates already in file)
    python sjc_gold_crawler.py --start 2025-01-01 --resume

Output CSV columns:
    date       YYYY-MM-DD
    buy        nghìn đồng / lượng (mua vào)
    sell       nghìn đồng / lượng (bán ra)
"""

import argparse
import csv
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sjc_crawler")

# ── Constants ─────────────────────────────────────────────────────────────────
SJC_URL      = "https://sjc.com.vn/bieu-do-gia-vang"
HCM_ROW      = 0        # Hồ Chí Minh is always the first data row in the table
MAX_HOLIDAY  = 120_000  # prices above this are stale cache from holidays → skip
WAIT_TIMEOUT = 15       # seconds to wait for page elements
PAGE_DELAY   = 2.5      # seconds to wait after clicking submit (ASP.NET postback)
REQUEST_GAP  = 0.5      # seconds between requests


# ── Data helpers ──────────────────────────────────────────────────────────────
def _to_float(text: str) -> Optional[float]:
    """'166,000' or '166.000' → 166000.0  |  empty / invalid → None"""
    if not text:
        return None
    cleaned = text.strip().replace(",", "").replace(".", "").replace(" ", "").replace("+", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _weekdays(start: date, end: date):
    """Yield Mon–Fri dates from start to end inclusive."""
    current = start
    while current <= end:
        if current.weekday() < 5:
            yield current
        current += timedelta(days=1)


# ── Scraper ───────────────────────────────────────────────────────────────────
def scrape(start: date, end: date, skip_dates: set = None) -> list[dict]:
    """
    Scrape SJC gold prices (Hồ Chí Minh only) for every trading day
    in [start, end]. Returns list of {"date", "buy", "sell"} dicts.

    skip_dates: set of ISO date strings to skip (for resume mode).
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup

    skip_dates = skip_dates or set()

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts,
    )
    wait    = WebDriverWait(driver, WAIT_TIMEOUT)
    records = []

    trading_days = [d for d in _weekdays(start, end) if d.isoformat() not in skip_dates]
    total        = len(trading_days)

    log.info("Loading SJC page…")
    driver.get(SJC_URL)
    wait.until(EC.presence_of_element_located((By.ID, "datesearch")))
    log.info("Page loaded. %d trading days to fetch.", total)

    try:
        for idx, current in enumerate(trading_days, 1):
            iso_str = current.isoformat()
            vn_str  = current.strftime("%d/%m/%Y")
            log.info("[%d/%d] %s …", idx, total, iso_str)

            # 1. Set date in text input (site expects DD/MM/YYYY)
            inp = wait.until(EC.element_to_be_clickable((By.ID, "datesearch")))
            inp.click()
            inp.send_keys(Keys.CONTROL + "a")
            inp.send_keys(Keys.DELETE)
            inp.clear()
            inp.send_keys(vn_str)
            time.sleep(0.2)

            # 2. Click "Tra cứu"
            btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.button-datesearch")
            ))
            btn.click()

            # 3. Wait for ASP.NET postback to re-render table
            time.sleep(PAGE_DELAY)

            # 4. Parse — take only the first data row (Hồ Chí Minh)
            soup  = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table")

            if not table:
                log.warning("  ⚠ No table found — skipping (holiday / no trading)")
                time.sleep(REQUEST_GAP)
                continue

            data_rows = []
            for row in table.find_all("tr"):
                cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                if len(cells) >= 4 and cells[0].isdigit():
                    data_rows.append(cells)

            if not data_rows:
                log.warning("  ⚠ Table has no data rows — skipping")
                time.sleep(REQUEST_GAP)
                continue

            hcm_cells = data_rows[HCM_ROW]
            buy_raw   = hcm_cells[2].split()[0] if len(hcm_cells) > 2 else ""
            sell_raw  = hcm_cells[3].split()[0] if len(hcm_cells) > 3 else ""
            buy       = _to_float(buy_raw)
            sell      = _to_float(sell_raw)

            # Skip stale holiday cache (price jumps to ~163,000 on Tết etc.)
            if buy and buy > MAX_HOLIDAY:
                log.warning("  ⚠ Price %.0f looks like stale holiday cache — skipping", buy)
                time.sleep(REQUEST_GAP)
                continue

            records.append({"date": iso_str, "buy": buy, "sell": sell})
            log.info("  ✓ buy=%-10s sell=%s",
                     f"{buy:,.0f}" if buy else "–",
                     f"{sell:,.0f}" if sell else "–")

            time.sleep(REQUEST_GAP)

    finally:
        driver.quit()

    log.info("Done. %d records collected from %d trading days.", len(records), total)
    return records


# ── CSV I/O ───────────────────────────────────────────────────────────────────
FIELDNAMES = ["date", "buy", "sell"]


def load_existing_dates(path: Path) -> set:
    """Return set of date strings already saved (for --resume)."""
    if not path.exists():
        return set()
    with open(path, encoding="utf-8-sig") as f:
        return {row["date"] for row in csv.DictReader(f)}


def save_csv(records: list[dict], path: Path, append: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append and path.exists() else "w"
    with open(path, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if mode == "w":
            writer.writeheader()
        writer.writerows(records)
    log.info("✅ %s %d rows → %s",
             "Appended" if mode == "a" else "Saved", len(records), path)


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    today = date.today()
    p = argparse.ArgumentParser(
        description="SJC Gold Price Crawler — Hồ Chí Minh, daily history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--start",  default="2025-01-01",
                   help="Start date YYYY-MM-DD (default: 2025-01-01)")
    p.add_argument("--end",    default=today.isoformat(),
                   help=f"End date YYYY-MM-DD (default: today {today})")
    p.add_argument("--output", default="sjc_gold_hcm.csv",
                   help="Output CSV file (default: sjc_gold_hcm.csv)")
    p.add_argument("--resume", action="store_true",
                   help="Skip dates already in output file and append new rows")
    return p.parse_args()


def main():
    args  = parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end   = datetime.strptime(args.end,   "%Y-%m-%d").date()
    out   = Path(args.output)

    if start > end:
        log.error("--start must be ≤ --end")
        raise SystemExit(1)

    skip = load_existing_dates(out) if args.resume else set()
    if skip:
        log.info("Resume mode: %d dates already saved — skipping them.", len(skip))

    records = scrape(start, end, skip_dates=skip)

    if not records:
        log.warning("No new records collected.")
        return

    save_csv(records, out, append=args.resume)


if __name__ == "__main__":
    main()
