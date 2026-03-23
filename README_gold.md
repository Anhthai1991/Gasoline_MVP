# SJC Gold Price Crawler

Crawl lịch sử giá vàng SJC (Hồ Chí Minh) từ [sjc.com.vn](https://sjc.com.vn/bieu-do-gia-vang) về file CSV.

## Cài đặt


> **Lưu ý:** Cần cài Chrome trước. `webdriver-manager` sẽ tự tải ChromeDriver tương thích.

## Sử dụng

```bash
# Crawl từ đầu năm 2025 đến hôm nay
python sjc_gold_crawler.py --start 2025-01-01

# Crawl khoảng thời gian tuỳ chỉnh
python sjc_gold_crawler.py --start 2024-01-01 --end 2024-12-31 --output gold_2024.csv

# Resume — bỏ qua ngày đã có, thêm ngày mới vào file cũ
python sjc_gold_crawler.py --start 2026-01-01 --resume
```

## Output

File CSV với 3 cột (đơn vị: **nghìn đồng / lượng**):

| date       | buy    | sell   |
|------------|--------|--------|
| 2025-01-02 | 82200  | 84200  |
| 2025-01-03 | 82200  | 84200  |
| 2025-01-06 | 84000  | 85500  |

## Lưu ý

- Chỉ crawl ngày **Thứ 2 – Thứ 6** (thị trường vàng đóng cửa cuối tuần)
- Ngày lễ / Tết: SJC hiển thị giá cache cũ → crawler tự **bỏ qua** các ngày có giá bất thường (> 120,000)
- Tốc độ: ~3 giây/ngày → 300 ngày ≈ 15 phút

## Cập nhật hàng ngày (tùy chọn)

Thêm vào crontab để tự động crawl mỗi buổi sáng:

```bash
# Chạy lúc 9:00 sáng mỗi ngày, append vào file cũ
0 9 * * 1-5 cd /path/to/sjc-gold-crawler && python sjc_gold_crawler.py --start 2026-01-01 --resume
```
