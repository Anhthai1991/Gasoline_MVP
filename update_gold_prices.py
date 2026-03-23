#!/usr/bin/env python3
"""
Gold Price Auto-Update Script
Crawls VN SJC gold prices and World XAU/USD daily prices.
Appends new rows to gold_prices.csv and commits to Git.

Data sources:
  - VN SJC: https://sjc.com.vn/xml/tygiavang.xml (official SJC XML feed)
  - World XAU/USD: https://query1.finance.yahoo.com/v8/finance/chart/GC=F (Yahoo Finance)
"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
import os
import subprocess
import sys
import json

# ── Config ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE   = os.path.join(SCRIPT_DIR, "gold_prices.csv")

SJC_XML_URL  = "https://sjc.com.vn/xml/tygiavang.xml"
YAHOO_URL    = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

GIT_COMMIT_MSG = "Auto-update gold prices - {date}"

# ── Helpers ──────────────────────────────────────────────────────────────────

def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def get_last_date_from_csv() -> datetime | None:
    """Return the last date already in gold_prices.csv, or None if file missing."""
    if not os.path.exists(CSV_FILE):
        return None
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty or "Date" not in df.columns:
            return None
        df["Date_dt"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
        return df["Date_dt"].max()
    except Exception as e:
        print(f"[WARNING] Could not read CSV: {e}")
        return None


# ── SJC Crawl ────────────────────────────────────────────────────────────────

def crawl_sjc() -> dict | None:
    """
    Fetch current SJC buy/sell price from official XML feed.
    Returns {'buy': int, 'sell': int} in VND/lượng, or None on error.
    SJC XML format:
      <item>
        <n>SJC 1L, 10L, 1KG</n>
        <ns>SJC</ns>
        <pb>13150</pb>  ← buy price (x 1000 VND)
        <ps>13200</ps>  ← sell price (x 1000 VND)
        ...
      </item>
    """
    try:
        print("[INFO] Fetching SJC gold price from sjc.com.vn...")
        resp = requests.get(SJC_XML_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        # Find the main SJC bar item (1L, 10L, 1KG)
        for item in root.iter("item"):
            name_el = item.find("n")
            ns_el   = item.find("ns")
            pb_el   = item.find("pb")
            ps_el   = item.find("ps")
            if name_el is None or pb_el is None or ps_el is None:
                continue
            name = (name_el.text or "").strip()
            if "1L" in name or "10L" in name:
                # Prices are in thousands VND per lượng; convert:
                # SJC website sometimes stores as e.g. "13150" meaning 13,150,000 VND
                buy_raw  = pb_el.text.strip().replace(",", "").replace(".", "")
                sell_raw = ps_el.text.strip().replace(",", "").replace(".", "")
                buy_val  = int(buy_raw)
                sell_val = int(sell_raw)
                # If values look like they're in thousands (e.g., < 1,000,000), multiply
                if buy_val < 1_000_000:
                    buy_val  *= 1_000
                    sell_val *= 1_000
                print(f"[SUCCESS] SJC Buy: {buy_val:,} VNĐ | Sell: {sell_val:,} VNĐ")
                return {"buy": buy_val, "sell": sell_val}

        print("[WARNING] Could not find SJC 1L item in XML.")
        return None

    except Exception as e:
        print(f"[ERROR] SJC crawl failed: {e}")
        return None


# ── Yahoo Finance XAU/USD ─────────────────────────────────────────────────────

def crawl_xauusd() -> float | None:
    """
    Fetch latest XAU/USD close price from Yahoo Finance API.
    Returns float (USD/troy oz) or None on error.
    """
    try:
        print("[INFO] Fetching XAU/USD from Yahoo Finance (GC=F)...")
        params = {
            "interval":  "1d",
            "range":     "5d",
            "includePrePost": "false",
        }
        resp = requests.get(YAHOO_URL, headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        # Last non-null close
        close = next((c for c in reversed(closes) if c is not None), None)
        if close is None:
            print("[WARNING] No valid close price in Yahoo response.")
            return None
        print(f"[SUCCESS] XAU/USD close: ${close:.2f}")
        return round(close, 2)

    except Exception as e:
        print(f"[ERROR] Yahoo Finance crawl failed: {e}")
        return None


# ── CSV Update ───────────────────────────────────────────────────────────────

def update_csv(date_str: str, sjc: dict | None, xauusd: float | None) -> bool:
    """Append today's data to gold_prices.csv."""
    try:
        # Build new row
        new_row = {
            "Date":      date_str,
            "SJC_Buy_VND":  sjc["buy"]  if sjc   else None,
            "SJC_Sell_VND": sjc["sell"] if sjc   else None,
            "XAU_USD":      xauusd      if xauusd else None,
        }
        df_new = pd.DataFrame([new_row])

        if os.path.exists(CSV_FILE):
            df_old = pd.read_csv(CSV_FILE)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
            # Deduplicate – keep last for each date
            df_all = df_all.drop_duplicates(subset=["Date"], keep="last")
            df_all = df_all.sort_values("Date")
        else:
            df_all = df_new

        df_all.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        print(f"[SUCCESS] gold_prices.csv updated ({len(df_all)} rows total).")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to update CSV: {e}")
        return False


# ── Git Commit & Push ────────────────────────────────────────────────────────

def git_commit_push():
    """Commit and push gold_prices.csv to GitHub."""
    try:
        is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
        git_user  = "github-actions[bot]" if is_ci else "Gold Price Bot"
        git_email = "github-actions[bot]@users.noreply.github.com" if is_ci else "bot@gold-update.local"

        subprocess.run(["git", "config", "user.name",  git_user],  check=False, capture_output=True, cwd=SCRIPT_DIR)
        subprocess.run(["git", "config", "user.email", git_email], check=False, capture_output=True, cwd=SCRIPT_DIR)
        subprocess.run(["git", "add", CSV_FILE], check=True, capture_output=True, cwd=SCRIPT_DIR)

        commit_msg = GIT_COMMIT_MSG.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"))
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, cwd=SCRIPT_DIR)
        subprocess.run(["git", "push"], check=True, capture_output=True, cwd=SCRIPT_DIR)
        print("[SUCCESS] Pushed to repository.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Git push failed: {e}")
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("Gold Price Auto-Update Script")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    today = today_str()

    # Skip if already updated today
    last_date = get_last_date_from_csv()
    if last_date is not None and last_date.strftime("%Y-%m-%d") == today:
        print(f"\n[INFO] Data for {today} already exists. Nothing to do.")
        sys.exit(0)

    # Step 1: Crawl SJC
    print("\n[STEP 1] VN SJC Gold Price")
    sjc = crawl_sjc()

    # Step 2: Crawl XAU/USD
    print("\n[STEP 2] World Gold XAU/USD")
    xauusd = crawl_xauusd()

    # Step 3: Update CSV
    print("\n[STEP 3] Updating CSV")
    if not update_csv(today, sjc, xauusd):
        sys.exit(1)

    # Step 4: Git commit
    print("\n[STEP 4] Git commit & push")
    git_commit_push()

    print("\n" + "="*60)
    print("Gold price update complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
