"""
update_gold_prices.py
=====================
Daily wrapper for the SJC gold price crawler.

Called automatically by GitHub Actions every weekday at 09:00 Vietnam time.

Logic:
  1. Đọc ngày cuối cùng đã có trong gold_prices.csv
  2. Crawl TẤT CẢ các ngày từ (ngày cuối + 1) đến hôm nay (chỉ T2–T6)
  3. APPEND vào gold_prices.csv — không bao giờ ghi đè dữ liệu cũ

Nếu CSV chưa tồn tại → crawl từ đầu năm hiện tại.
Nếu mọi ngày đã có → thoát sớm, không thay đổi gì.

Usage:
    python update_gold_prices.py

    # Crawl lại từ ngày cụ thể (bỏ qua ngày đã có):
    python update_gold_prices.py --since 2026-01-01
"""

import argparse
import csv
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Reuse crawler helpers ──────────────────────────────────────────────────────
from sjc_gold_crawler import scrape, load_existing_dates

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_CSV   = Path("gold_prices.csv")
FIELDNAMES   = ["date", "buy", "sell", "source"]
SOURCE_TAG   = "sjc.com.vn"
DEFAULT_FROM = date(date.today().year, 1, 1)   # đầu năm hiện tại nếu CSV trống

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("update_gold")


# ── Helpers ───────────────────────────────────────────────────────────────────

def last_date_in_csv(path: Path):
    """Trả về date object của dòng cuối cùng trong CSV, hoặc None nếu chưa có."""
    existing = load_existing_dates(path)   # set of ISO strings
    if not existing:
        return None
    return max(datetime.strptime(d, "%Y-%m-%d").date() for d in existing)


def next_weekday(d: date) -> date:
    """Trả về ngày làm việc kế tiếp sau d (bỏ qua T7, CN)."""
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt


def last_weekday(d: date) -> date:
    """Trả về d nếu là T2–T6, ngược lại lùi về thứ 6 gần nhất."""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def append_records(records: list[dict], path: Path):
    """APPEND danh sách records vào CSV — không bao giờ truncate file cũ."""
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    need_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if need_header:
            writer.writeheader()
        for row in records:
            writer.writerow({
                "date":   row["date"],
                "buy":    row["buy"],
                "sell":   row["sell"],
                "source": SOURCE_TAG,
            })
    log.info("✅ Appended %d row(s) to %s.", len(records), path)


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="SJC Gold Price Daily Updater")
    p.add_argument(
        "--since",
        default=None,
        help="Crawl từ ngày này (YYYY-MM-DD). Mặc định: ngày kế tiếp sau dòng cuối trong CSV",
    )
    return p.parse_args()


def main():
    args  = parse_args()
    today = last_weekday(date.today())

    # Xác định ngày bắt đầu crawl
    if args.since:
        start = datetime.strptime(args.since, "%Y-%m-%d").date()
        log.info("--since flag: crawl from %s.", start)
    else:
        last = last_date_in_csv(OUTPUT_CSV)
        if last is None:
            start = DEFAULT_FROM
            log.info("CSV empty/missing — crawl from %s (start of year).", start)
        else:
            start = next_weekday(last)
            log.info("Last date in CSV: %s — start from %s.", last, start)

    if start > today:
        log.info("✅ All dates up to %s already recorded. Nothing to do.", today)
        sys.exit(0)

    log.info("Crawling %s → %s (weekdays only)…", start, today)

    # Load existing dates để skip (tránh duplicate khi dùng --since)
    skip = load_existing_dates(OUTPUT_CSV)
    records = scrape(start, today, skip_dates=skip)

    if not records:
        log.warning("⚠ No new records returned (all holidays or already recorded).")
        sys.exit(0)

    append_records(records, OUTPUT_CSV)


if __name__ == "__main__":
    main()
