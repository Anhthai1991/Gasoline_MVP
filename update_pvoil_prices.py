#!/usr/bin/env python3
"""
PVOIL Price Update Script (FIXED VERSION)
Automatically crawls and updates gasoline prices from PVOIL website
FIXES:
- Correct column indices for fuel type and price
- Better date parsing from website
- Improved error handling and debugging
- Proper data structure for CSV export
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import subprocess
import sys
import re
import csv

# Configuration
PVOIL_URL = "https://www.pvoil.com.vn/tin-gia-xang-dau"
CSV_FILE = "pvoil_gasoline_prices_full.csv"
GIT_COMMIT_MESSAGE = "Auto-update PVOIL fuel prices - {date}"

# Hàm lấy tất cả các ngày có trên website PVOIL

def get_dates_from_website():
    """
    Extract all available dates from PVOIL website
    Returns: list of dates in DD/MM/YYYY HH:MM:SS format
    """
    try:
        print("\n[INFO] Fetching dates from PVOIL website...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(PVOIL_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract dates in DD-MM-YYYY format
        date_pattern = re.compile(r'\b\d{2}-\d{2}-\d{4}\b')
        dates_raw = date_pattern.findall(soup.get_text())
        
        # Convert to DD/MM/YYYY 15:00:00 format for API
        dates = [d.replace('-', '/') + ' 15:00:00' for d in dates_raw]
        dates = sorted(list(set(dates)), reverse=True)  # Remove duplicates, sort descending
        
        print(f"[SUCCESS] Found {len(dates)} unique dates")
        return dates
        
    except Exception as e:
        print(f"[ERROR] Failed to get dates: {e}")
        return []

# Thêm hàm đọc ngày cuối cùng từ CSV để so sánh

def get_last_date_from_csv():
    if not os.path.exists(CSV_FILE):
        return None
    
    df = pd.read_csv(CSV_FILE)
    # cột 'Ngày' đang dạng DD/MM/YYYY
    df["Ngày_dt"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y")
    return df["Ngày_dt"].max()

# Hàm crawl giá cho một ngày cụ thể

def crawl_pvoil_prices_by_date(date_str):
    """
    Crawl price data for specific date from API
    Args: date_str in format DD/MM/YYYY HH:MM:SS
    Returns: list of [date, fuel_type, price] or []
    """
    try:
        api_url = f'https://www.pvoil.com.vn/api/oilprice/load-view?date={requests.utils.quote(date_str)}'
        print(f"[INFO] Fetching prices for {date_str.split()[0]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print(f"[WARNING] No table found for date {date_str}")
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header row
        data_rows = []
        
        for row in rows:
            cells = row.find_all('td')
            
            # Debug: print cell count and content
            if len(cells) == 0:
                continue
                
            # Print structure for debugging (first row)
            if not data_rows:
                print(f"[DEBUG] Row structure: {len(cells)} cells")
                for idx, cell in enumerate(cells):
                    print(f"  Cell {idx}: {cell.get_text(strip=True)[:50]}")
            
            # FIXED: Correct column indices
            # Based on CSV analysis: [0]=STT, [1]=Fuel Name, [2]=Unit, [3]=Price
            if len(cells) >= 4:
                try:
                    fuel_type = cells[1].get_text(strip=True)
                    price_str = cells[2].get_text(strip=True)  # FIXED: Changed from cells[3] to cells[2]
                    # Clean price: remove VND symbol, dots, commas
                    price_clean = price_str.replace('đ', '').replace('.', '').replace(',', '').strip()
                    
                    # Validate price is numeric
                    if price_clean and price_clean.isdigit():
                        date_only = date_str.split()[0]  # Get DD/MM/YYYY part
                        data_rows.append([date_only, fuel_type, price_clean])
                    else:
                        print(f"[WARNING] Invalid price format: {price_str}")
                        
                except (IndexError, ValueError) as e:
                    print(f"[WARNING] Error parsing row: {e}")
                    continue
        
        if data_rows:
            print(f"[SUCCESS] Extracted {len(data_rows)} price records for {date_str.split()[0]}")
        else:
            print(f"[WARNING] No valid price data extracted for {date_str}")
            
        return data_rows
        
    except Exception as e:
        print(f"[ERROR] Failed to crawl prices for {date_str}: {e}")
        return []

# Hàm crawl tất cả các ngày > ngày cuối cùng trong CSV

def crawl_all_prices():
    """
    Crawl all available prices from PVOIL website
    Returns: list of [date, fuel_type, price] records
    """
    dates = get_dates_from_website()
    if not dates:
        print("[ERROR] No dates found. Cannot proceed.")
        return []

    last_date = get_last_date_from_csv()
    print(f"[INFO] Last date in CSV: {last_date}")

    # chuyển về datetime để so sánh
    dates_dt = []
    for d in dates:
        d_only = d.split()[0]          # "DD/MM/YYYY"
        dt = datetime.strptime(d_only, "%d/%m/%Y")
        dates_dt.append((dt, d))

    # nếu chưa có file thì crawl hết
    if last_date is not None:
        dates_dt = [x for x in dates_dt if x[0] > last_date]

    if not dates_dt:
        print("[INFO] No new dates to crawl.")
        return []

    all_data = []
    for dt, date_str in dates_dt:
        data = crawl_pvoil_prices_by_date(date_str)
        all_data.extend(data)

    return all_data


def update_csv(data):
    """
    data: list of [date, fuel_type, price] CHỈ cho các ngày mới
    """
    try:
        print(f"\n[INFO] Updating CSV file: {CSV_FILE}")
        df_new = pd.DataFrame(data, columns=['Ngày', 'Mặt hàng', 'Giá (VND)'])

        if os.path.exists(CSV_FILE):
            df_old = pd.read_csv(CSV_FILE)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
            df_all = df_all.drop_duplicates(subset=['Ngày', 'Mặt hàng'], keep='last')
        else:
            df_all = df_new

        df_all.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        print(f"[SUCCESS] CSV updated successfully. Total records: {len(df_all)}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to update CSV: {e}")
        return False


def git_commit_push():
    """
    Commit and push changes to Git repository
    """
    try:
        # Configure git
        subprocess.run(['git', 'config', 'user.name', 'PVOIL Auto-Update Bot'], 
                      check=False, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'bot@pvoil-update.local'], 
                      check=False, capture_output=True)
        
        # Add changes
        print("\n[INFO] Adding changes to git...")
        subprocess.run(['git', 'add', CSV_FILE], check=True, capture_output=True)
        
        # Commit
        commit_msg = GIT_COMMIT_MESSAGE.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))
        print(f"[INFO] Committing: {commit_msg}")
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
        
        # Push
        print("[INFO] Pushing to remote repository...")
        subprocess.run(['git', 'push'], check=True, capture_output=True)
        
        print("[SUCCESS] Successfully pushed to repository")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Git operation failed: {e}")
        print("[INFO] This may be expected if running locally without git setup")
        return False

def main():
    """
    Main execution function
    """
    print("\n" + "="*60)
    print("PVOIL Price Auto-Update Script (FIXED VERSION)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Step 1: Crawl all prices
    print("\n[STEP 1] Crawling prices from PVOIL website...")
    all_data = crawl_all_prices()
    
    if not all_data:
        print("\n[ERROR] Failed to crawl any price data. Exiting.")
        sys.exit(1)
    
    print(f"\n[SUCCESS] Crawled {len(all_data)} total records")
    
    # Step 2: Update CSV
    print("\n[STEP 2] Updating CSV file...")
    if not update_csv(all_data):
        print("\n[ERROR] Failed to update CSV. Exiting.")
        sys.exit(1)
    
    # Step 3: Git commit and push
    print("\n[STEP 3] Committing and pushing to Git...")
    git_commit_push()
    
    print("\n" + "="*60)
    print("Update completed successfully!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
