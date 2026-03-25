"""
SJC Gold Price History Crawler
================================
Crawls daily gold prices (Hồ Chí Minh) from sjc.com.vn/bieu-do-gia-vang.

Strategy:
  - Bỏ qua ngày lễ VN chính thức (thị trường không hoạt động)
  - Lấy nguyên giá thật, KHÔNG filter theo ngưỡng giá
  - Chỉ skip khi trang trả về bảng rỗng (thực sự không có dữ liệu)

Confirmed DOM (March 2026):
  - Date input : id="datesearch"  type="text"  format DD/MM/YYYY
  - Submit btn : class="button-datesearch"  text="Tra cứu"
  - Page stack : ASP.NET WebForms

Requirements:
    pip install selenium webdriver-manager beautifulsoup4

Usage:
    python sjc_gold_crawler.py --start 2025-01-01
    python sjc_gold_crawler.py --start 2024-01-01 --end 2025-12-31 --output gold_2024.csv
    python sjc_gold_crawler.py --start 2025-01-01 --resume

Output CSV columns:
    date    YYYY-MM-DD
    buy     nghìn đồng / lượng (mua vào)
    sell    nghìn đồng / lượng (bán ra)
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
HCM_ROW      = 0     # Hồ Chí Minh luôn là dòng đầu tiên trong bảng
WAIT_TIMEOUT = 15    # giây chờ element xuất hiện
PAGE_DELAY   = 2.5   # giây chờ ASP.NET postback re-render bảng
REQUEST_GAP  = 0.5   # giây nghỉ giữa các request


# ── Vietnamese public holidays ────────────────────────────────────────────────
def vn_holidays(year: int) -> set[date]:
    """
    Trả về tập hợp các ngày lễ chính thức của Việt Nam trong năm `year`.
    Áp dụng Luật Lao động VN (9 ngày lễ cố định + nghỉ bù nếu trùng cuối tuần).

    Lưu ý Tết Âm lịch: ngày âm lịch thay đổi mỗi năm — cần cập nhật thủ công.
    Danh sách dưới đây đã bao gồm 2024–2028.
    """
    # Ngày lễ dương lịch cố định
    fixed = [
        date(year, 1, 1),    # Tết Dương lịch
        date(year, 4, 30),   # Giải phóng miền Nam
        date(year, 5, 1),    # Quốc tế Lao động
        date(year, 9, 2),    # Quốc khánh
    ]

    # Giỗ Tổ Hùng Vương: 10/3 Âm lịch — ngày dương lịch theo từng năm
    hung_vuong = {
        2024: date(2024, 4, 18),
        2025: date(2025, 4, 7),
        2026: date(2026, 3, 28),
        2027: date(2027, 4, 16),
        2028: date(2028, 4, 4),
    }

    # Tết Nguyên Đán: thường nghỉ ~7 ngày (29 tháng Chạp → mùng 5 tháng Giêng)
    tet_ranges = {
        2024: (date(2024, 2, 8),  date(2024, 2, 14)),
        2025: (date(2025, 1, 25), date(2025, 2, 2)),
        2026: (date(2026, 1, 28), date(2026, 2, 5)),
        2027: (date(2027, 2, 15), date(2027, 2, 21)),
        2028: (date(2028, 2, 4),  date(2028, 2, 10)),
    }

    # Ngày lễ điểm: có áp dụng nghỉ bù nếu trùng cuối tuần
    point_holidays = set(fixed)
    if year in hung_vuong:
        point_holidays.add(hung_vuong[year])

    # Tết: range liên tục — không bù thêm (đã nghỉ đủ ngày trong range)
    tet_days = set()
    if year in tet_ranges:
        s, e = tet_ranges[year]
        d = s
        while d <= e:
            tet_days.add(d)
            d += timedelta(days=1)

    # Nghỉ bù chỉ cho ngày lễ điểm
    compensations = set()
    for h in point_holidays:
        if h.weekday() == 5:   # Thứ 7 → bù Thứ 6 trước
            compensations.add(h - timedelta(days=1))
        elif h.weekday() == 6: # Chủ nhật → bù Thứ 2 sau
            compensations.add(h + timedelta(days=1))

    return point_holidays | tet_days | compensations


def is_vn_holiday(d: date) -> bool:
    return d in vn_holidays(d.year)


# ── Data helpers ──────────────────────────────────────────────────────────────
def _to_float(text: str) -> Optional[float]:
    """'166,000' hoặc '166.000' → 166000.0  |  rỗng / lỗi → None"""
    if not text:
        return None
    cleaned = text.strip().replace(",", "").replace(".", "").replace(" ", "").replace("+", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _trading_days(start: date, end: date) -> list[date]:
    """Trả về danh sách ngày Thứ 2–6, không phải ngày lễ VN."""
    result = []
    current = start
    while current <= end:
        if current.weekday() < 5 and not is_vn_holiday(current):
            result.append(current)
        else:
            if current.weekday() < 5:
                log.debug("  Bỏ qua %s — ngày lễ VN", current)
        current += timedelta(days=1)
    return result


# ── Scraper ───────────────────────────────────────────────────────────────────
def scrape(start: date, end: date, skip_dates: set = None) -> list[dict]:
    """
    Cào giá vàng SJC (Hồ Chí Minh) cho mỗi ngày giao dịch trong [start, end].
    Trả về list các dict {"date", "buy", "sell"}.

    skip_dates: tập ngày ISO đã có trong file (dùng cho --resume).
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

    days  = [d for d in _trading_days(start, end) if d.isoformat() not in skip_dates]
    total = len(days)

    log.info("Loading SJC page…")
    driver.get(SJC_URL)
    wait.until(EC.presence_of_element_located((By.ID, "datesearch")))
    log.info("Page loaded. %d ngày giao dịch cần cào.", total)

    try:
        for idx, current in enumerate(days, 1):
            iso_str = current.isoformat()
            vn_str  = current.strftime("%d/%m/%Y")
            log.info("[%d/%d] %s …", idx, total, iso_str)

            # 1. Nhập ngày vào ô tìm kiếm (định dạng DD/MM/YYYY)
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

            # 3. Chờ ASP.NET postback re-render bảng
            time.sleep(PAGE_DELAY)

            # 4. Parse — chỉ lấy dòng đầu (Hồ Chí Minh)
            soup  = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table")

            if not table:
                log.warning("  ⚠ Không tìm thấy bảng — bỏ qua")
                time.sleep(REQUEST_GAP)
                continue

            data_rows = []
            for row in table.find_all("tr"):
                cells = [td.get_text(separator=" ", strip=True) for td in row.find_all("td")]
                if len(cells) >= 4 and cells[0].isdigit():
                    data_rows.append(cells)

            if not data_rows:
                log.warning("  ⚠ Bảng không có dữ liệu — bỏ qua")
                time.sleep(REQUEST_GAP)
                continue

            hcm   = data_rows[HCM_ROW]
            buy   = _to_float(hcm[2].split()[0] if len(hcm) > 2 else "")
            sell  = _to_float(hcm[3].split()[0] if len(hcm) > 3 else "")

            # Lấy nguyên giá — KHÔNG filter theo ngưỡng
            records.append({"date": iso_str, "buy": buy, "sell": sell})
            log.info("  ✓ buy=%-10s sell=%s",
                     f"{buy:,.0f}" if buy else "–",
                     f"{sell:,.0f}" if sell else "–")

            time.sleep(REQUEST_GAP)

    finally:
        driver.quit()

    log.info("Hoàn tất. %d bản ghi / %d ngày giao dịch.", len(records), total)
    return records


# ── CSV I/O ───────────────────────────────────────────────────────────────────
FIELDNAMES = ["date", "buy", "sell"]


def load_existing_dates(path: Path) -> set:
    """Đọc các ngày đã có trong file CSV (dùng cho --resume)."""
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
    log.info("✅ %s %d dòng → %s",
             "Append" if mode == "a" else "Saved", len(records), path)


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    today = date.today()
    p = argparse.ArgumentParser(
        description="SJC Gold Price Crawler — Hồ Chí Minh, lịch sử ngày",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--start",  default="2025-01-01",
                   help="Ngày bắt đầu YYYY-MM-DD (mặc định: 2025-01-01)")
    p.add_argument("--end",    default=today.isoformat(),
                   help=f"Ngày kết thúc YYYY-MM-DD (mặc định: hôm nay {today})")
    p.add_argument("--output", default="sjc_gold_hcm.csv",
                   help="File CSV đầu ra (mặc định: sjc_gold_hcm.csv)")
    p.add_argument("--resume", action="store_true",
                   help="Bỏ qua ngày đã có trong file, append thêm dòng mới")
    return p.parse_args()


def main():
    args  = parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end   = datetime.strptime(args.end,   "%Y-%m-%d").date()
    out   = Path(args.output)

    if start > end:
        log.error("--start phải ≤ --end")
        raise SystemExit(1)

    skip = load_existing_dates(out) if args.resume else set()
    if skip:
        log.info("Resume: %d ngày đã có — bỏ qua.", len(skip))

    records = scrape(start, end, skip_dates=skip)

    if not records:
        log.warning("Không thu thập được dữ liệu mới.")
        return

    save_csv(records, out, append=args.resume)


if __name__ == "__main__":
    main()
