# PVOIL Price Auto-Update Script - Hướng Dẫn Sử Dụng

## Giới Thiệu

`update_pvoil_prices.py` là script Python tự động cập nhật giá xăng dầu từ website PVOIL và đẩy thay đổi lên GitHub repository.

## Tính Năng

✅ **Tự động crawl** dữ liệu giá xăng dầu mới từ PVOIL  
✅ **Cập nhật CSV** - Thêm dữ liệu mới vào file `pvoil_gasoline_prices_full.csv`  
✅ **Git automation** - Tự động commit và push lên repository  
✅ **Error handling** - Xử lý lỗi và báo cáo chi tiết

## Yêu Cầu Hệ Thống

### Dependencies

```bash
pip install requests beautifulsoup4 pandas
```

### Cấu Hình Git

Đảm bảo Git đã được cấu hình với quyền push:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Và đã thiết lập authentication (SSH key hoặc personal access token).

## Cách Sử Dụng

### 1. Chạy Thủ Công

```bash
python update_pvoil_prices.py
```

### 2. Chạy Tự Động với Cron (Linux/Mac)

Chạy mỗi ngày lúc 8:00 sáng:

```bash
crontab -e
```

Thêm dòng:

```
0 8 * * * cd /path/to/Fuel-VN-price && python update_pvoil_prices.py >> update.log 2>&1
```

### 3. Chạy Tự Động với GitHub Actions

Tạo file `.github/workflows/auto-update.yml`:

```yaml
name: Auto Update PVOIL Prices

on:
  schedule:
    - cron: '0 1 * * *'  # Chạy mỗi ngày lúc 1:00 AM UTC
  workflow_dispatch:  # Cho phép chạy manual

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4 pandas
      
      - name: Run update script
        run: |
          python update_pvoil_prices.py
```

### 4. Chạy với Task Scheduler (Windows)

1. Mở Task Scheduler
2. Tạo Basic Task
3. Trigger: Daily
4. Action: Start a program
   - Program: `python`
   - Arguments: `update_pvoil_prices.py`
   - Start in: `/path/to/Fuel-VN-price`

## Cấu Trúc Script

### Các Hàm Chính

#### `crawl_pvoil_prices()`
Crawl dữ liệu giá xăng từ website PVOIL.

**Returns:** Dictionary chứa dữ liệu giá hoặc `None` nếu lỗi.

#### `update_csv(price_data)`
Cập nhật file CSV với dữ liệu mới.

**Parameters:**
- `price_data` (dict): Dữ liệu giá cần thêm vào CSV

**Returns:** `True` nếu thành công, `False` nếu lỗi.

#### `git_commit_push()`
Commit và push thay đổi lên remote repository.

**Returns:** `True` nếu thành công, `False` nếu lỗi.

## Tùy Chỉnh

### Thay Đổi URL Nguồn

```python
PVOIL_URL = "https://www.pvoil.com.vn/your-custom-url"
```

### Thay Đổi Tên File CSV

```python
CSV_FILE = "your_custom_filename.csv"
```

### Tùy Chỉnh Commit Message

```python
GIT_COMMIT_MESSAGE = "Updated: {date} - Custom message"
```

## Xử Lý Lỗi

Script sẽ tự động xử lý và báo lỗi:

- ❌ **Crawl failed** → Kiểm tra kết nối internet và URL
- ❌ **CSV update failed** → Kiểm tra quyền ghi file
- ❌ **Git push failed** → Kiểm tra authentication và quyền push

## Log và Debug

Chạy với output chi tiết:

```bash
python update_pvoil_prices.py 2>&1 | tee update.log
```

## Best Practices

1. ✅ Test script thủ công trước khi schedule tự động
2. ✅ Kiểm tra log định kỳ để phát hiện lỗi sớm
3. ✅ Backup file CSV định kỳ
4. ✅ Sử dụng Git authentication an toàn (SSH keys, PAT)
5. ✅ Set up notifications khi script fail

## Troubleshooting

### Script không crawl được dữ liệu

- Kiểm tra website PVOIL có thay đổi cấu trúc HTML không
- Update CSS selectors trong hàm `crawl_pvoil_prices()`

### Git push bị từ chối

```bash
# Kiểm tra authentication
git config --list

# Setup SSH key hoặc use personal access token
git remote set-url origin https://TOKEN@github.com/Anhthai1991/Fuel-VN-price.git
```

### Dependencies lỗi

```bash
# Reinstall dependencies
pip install --upgrade requests beautifulsoup4 pandas
```

## Liên Hệ & Đóng Góp

Nếu gặp vấn đề hoặc có đề xuất cải tiến, vui lòng tạo issue trên GitHub.

---

**Version:** 1.0  
**Last Updated:** November 2025  
**Author:** Anhthai1991
