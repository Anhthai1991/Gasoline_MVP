# PVOIL Oil Price Tracker - Complete Project 🛢️

Professional oil price tracking system with automated updates, interactive dashboard, and comprehensive data analysis. Data updated automatically every 7 days.

## 🎯 Project Overview

**What it does:**
- ✅ Tracks PVOIL oil prices from 2019-2025 (1,152 data points)
- ✅ Displays live prices in professional dashboard
- ✅ Auto-updates every 7 days at 15:00 Vietnam time
- ✅ Interactive charts with date range filtering
- ✅ Export data in CSV format
- ✅ Historical trend analysis

**Data:**
- 📊 10 products tracked
- 📅 249 unique dates
- 🌍 Data from 2019-2025
- 📈 High/Low/Average statistics

## 📁 Project Structure

```
pvoil-price-tracker/
├── index.html                          # Main dashboard
├── styles.css                          # Professional styling
├── script.js                           # Interactive features
├── pvoil_gasoline_prices_full.csv      # Your data (auto-updated)
├── pvoil_updater.py                    # Update script
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
│
├── .github/
│   └── workflows/
│       └── update-pvoil-prices.yml     # GitHub Actions (7-day auto-update)
│
├── exports/
│   └── oil_prices_*.csv               # Exported data by date range
│
└── docs/
    ├── SETUP_GUIDE.md                 # Quick start
    └── UPDATE_REPORT.md               # Auto-generated reports
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/pvoil-price-tracker.git
cd pvoil-price-tracker

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run Dashboard

**Option A: Direct (No server needed)**
```bash
# Just open index.html in your browser
open index.html
```

**Option B: Local server**
```bash
python -m http.server 8000
# Visit: http://localhost:8000
```

### 3. Update Prices (Manual)

```bash
python pvoil_updater.py
```

**Output:**
```
✅ Loaded 1152 existing records
📅 Latest date in CSV: 31/10/2024
📡 Fetching new prices...
✅ Added 5 new price records for 03/11/2025
✅ Saved CSV: pvoil_gasoline_prices_full.csv
📊 Total records: 1157
```

### 4. Deploy to GitHub

```bash
# Create repository on GitHub
git add .
git commit -m "PVOIL Price Tracker - Complete project"
git push origin main
```

**Then enable GitHub Pages:**
- Settings → Pages → Deploy from main branch
- Your dashboard: `https://Anhthai1991.github.io/Fuel-VN-price`

## 📊 Dashboard Features

### Current Prices (Cards)
- Live prices for main products
- Last update date
- Price indicators (up/down)
- Clean, professional display

### Interactive Charts
- Line chart with multiple products
- Date range filtering:
  - 1M (1 month)
  - 3M (3 months)
  - 6M (6 months)
  - 1Y (1 year)
  - 3Y (3 years)
  - ALL (2019-2025)
- Hover for details
- Zoom/Pan capability

### Statistics Panel
- Highest price (with date)
- Lowest price (with date)
- Average price
- Price volatility
- Trend analysis

### Data Table
- All prices in sortable table
- Filter by product
- Search by date
- Export to CSV

### Market Insights
- Key historical events
- Notable price movements
- Trend interpretations

## 🔄 Automatic Updates (GitHub Actions)

### How it works:
1. **Daily check** at 08:00 UTC (15:00 Vietnam time)
2. **Smart logic**: Only updates if ≥7 days since last update
3. **Auto-commit**: New data committed automatically
4. **Report generation**: Creates UPDATE_REPORT.md
5. **Zero maintenance**: Completely automated

### Schedule:
```
⏰ Time: 15:00 Vietnam time (08:00 UTC)
📅 Frequency: Every 7 days
🔄 Auto-commit: Yes
📊 Report: Generated automatically
```

### Manual Trigger:
GitHub → Actions → "Update PVOIL Oil Prices" → "Run workflow"

## 📈 Data Structure

### CSV Format
```csv
Ngày,Mặt hàng,Giá (VND)
31/12/2019,Xăng RON 95-III,20990
31/12/2019,Xăng E5 RON 92-II,19880
31/12/2019,Dầu DO 0,05S-II,16590
...
```

### Products Tracked

| Product | Code | Unit | Status |
|---------|------|------|--------|
| Xăng RON 95-III | xang_ron95_iii | VNĐ/lít | ✅ |
| Xăng E5 RON 92-II | xang_e5_ron92_ii | VNĐ/lít | ✅ |
| Dầu DO 0,05S-II | dau_do_005s_ii | VNĐ/lít | ✅ |
| Dầu KO | dau_ko | VNĐ/lít | ✅ |
| Dầu DO 0,001S-V | dau_do_001s_v | VNĐ/lít | ✅ |
| Xăng E10 RON 95-III | xang_e10_ron95_iii | VNĐ/lít | ✅ |
| + 4 more products | ... | VNĐ/lít | ✅ |

## 📊 Historical Statistics

### Price Ranges (All Time: 2019-2025)

**Xăng RON 95-III:**
- 🔺 Highest: 32,870 VNĐ/lít
- 🔻 Lowest: 11,630 VNĐ/lít
- 📊 Average: 21,488 VNĐ/lít

**Xăng E5 RON 92-II:**
- 🔺 Highest: 31,300 VNĐ/lít
- 🔻 Lowest: 10,940 VNĐ/lít
- 📊 Average: 20,549 VNĐ/lít

**Dầu DO 0,05S-II:**
- 🔺 Highest: 30,010 VNĐ/lít
- 🔻 Lowest: 9,850 VNĐ/lít
- 📊 Average: 18,651 VNĐ/lít

### Key Historical Events

📍 **April 2020 - COVID-19**
- Oil prices crashed to lowest point
- Global pandemic impact

📍 **June 2022 - Energy Crisis**
- Prices reached all-time high
- Russia-Ukraine war impact
- OPEC production cuts

📍 **2024-2025 - Stabilization**
- Prices stabilizing
- Current trend: Moderate

## 🔧 Technical Details

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Responsive design, Grid/Flexbox
- **JavaScript**: Vanilla (no frameworks)
- **Chart.js**: Data visualization
- **Papa Parse**: CSV parsing
- **Date.js**: Date handling

### Backend (Automation)
- **Python 3.11**: Main scraper
- **requests**: HTTP requests
- **BeautifulSoup4**: HTML parsing
- **GitHub Actions**: Scheduling & automation
- **Git**: Version control & commits

### Data
- **Format**: CSV (text-based, Git-friendly)
- **Storage**: GitHub repository
- **Backup**: Git history
- **Capacity**: Unlimited (database-ready)

## 🛠️ Troubleshooting

### Q: Dashboard doesn't load data
**A:** Make sure CSV file is in same folder as index.html
```bash
ls -la pvoil_gasoline_prices_full.csv
```

### Q: GitHub Actions doesn't run
**A:** Check:
1. `.github/workflows/update-pvoil-prices.yml` exists
2. Repository settings → Actions enabled
3. Check Actions tab for logs

### Q: PVOIL website changed
**A:** Update selectors in `pvoil_updater.py`:
```python
# Find new table selector
table = soup.find('table', {'class': 'new-class'})
```

### Q: CSV file corrupted
**A:** Restore from Git history:
```bash
git checkout HEAD -- pvoil_gasoline_prices_full.csv
```

## 📚 Useful Commands

### View update history
```bash
git log --oneline pvoil_gasoline_prices_full.csv
```

### Export data for Excel
```bash
# Use dashboard Export button or:
cp pvoil_gasoline_prices_full.csv my_export.csv
```

### Check last update time
```bash
git log -1 --format=%ai -- pvoil_gasoline_prices_full.csv
```

### Manual update
```bash
python pvoil_updater.py && git add . && git commit -m "Manual update" && git push
```

## 🎨 Customization

### Change update frequency
Edit `.github/workflows/update-pvoil-prices.yml`:
```yaml
# Current: Every 7 days
# Change 7 to desired days:
DAYS_DIFF=$(( ($CURRENT_TIME - $LAST_COMMIT) / 86400 ))
if [ "$DAYS_DIFF" -ge 7 ]; then  # ← Change 7 here
```

### Change update time
Edit workflow cron:
```yaml
# Current: 15:00 Vietnam = 08:00 UTC
- cron: '0 8 * * *'  # ← Change time here
# Format: minute hour day month dayofweek
```

### Add new products
Edit `pvoil_updater.py`:
```python
PRODUCTS = {
    'New Product': 'new_product_code',
    # ...
}
```

## 📈 Future Enhancements

- [ ] Email alerts on price changes
- [ ] Telegram/Discord notifications
- [ ] Database backend (SQLite/PostgreSQL)
- [ ] REST API for integration
- [ ] Mobile app
- [ ] Machine learning predictions
- [ ] Price comparison with competitors
- [ ] Historical yearly reports

## 📄 License

MIT License - Free for personal and commercial use

## 🙏 References

- [PVOIL Official](https://www.pvoil.com.vn)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Chart.js Documentation](https://www.chartjs.org)
- [Papa Parse Documentation](https://www.papaparse.com)

## 💬 Support

- 🐛 Found a bug? Open an issue
- 💡 Have an idea? Create a discussion
- 🔗 Want to contribute? Submit a PR

---

**Project Status:** ✅ Production Ready  
**Last Updated:** November 3, 2025  
**Version:** 1.0.0  
**Auto-Updates:** Every 7 days at 15:00 Vietnam time  

⭐ If you find this useful, please star the repository!
