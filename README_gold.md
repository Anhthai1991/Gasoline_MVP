# SJC Gold Price Crawler

Crawl lịch sử giá vàng SJC (Hồ Chí Minh) từ [sjc.com.vn](https://sjc.com.vn/bieu-do-gia-vang) về file CSV, sử dụng headless Chrome.

## Yêu cầu

- Python 3.10+
- Google Chrome đã cài sẵn trên máy (`webdriver-manager` tự tải ChromeDriver phù hợp)

## Cài đặt

```bash
git clone https://github.com/your-username/sjc-gold-crawler.git
cd sjc-gold-crawler
pip install -r requirements.txt
```

## Sử dụng

```bash
# Crawl từ ngày bắt đầu đến hôm nay
python sjc_gold_crawler.py --start 2025-01-01

# Crawl khoảng thời gian tuỳ chỉnh, lưu ra file riêng
python sjc_gold_crawler.py --start 2024-01-01 --end 2024-12-31 --output gold_2024.csv

# Resume — bỏ qua ngày đã có trong file, append thêm dòng mới
python sjc_gold_crawler.py --start 2025-01-01 --resume
```

## Output

File CSV với 3 cột, đơn vị **nghìn đồng / lượng**:

| date       | buy    | sell   |
|------------|--------|--------|
| 2026-01-02 | 150800 | 152800 |
| 2026-01-05 | 155100 | 157100 |
| 2026-01-06 | 156000 | 158000 |

## Cơ chế lọc ngày

Crawler bỏ qua đúng 2 loại ngày, không filter theo ngưỡng giá:

**Cuối tuần** — Thứ 7 và Chủ nhật (thị trường vàng không hoạt động).

**Ngày lễ Việt Nam chính thức** — được định nghĩa cứng trong hàm `vn_holidays()`:

| Ngày lễ | Ghi chú |
|---|---|
| 1/1 | Tết Dương lịch |
| Tết Nguyên Đán | Range ~7 ngày, thay đổi theo năm Âm lịch |
| 10/3 Âm lịch | Giỗ Tổ Hùng Vương, thay đổi theo năm |
| 30/4 | Giải phóng miền Nam |
| 1/5 | Quốc tế Lao động |
| 2/9 | Quốc khánh |

Ngày lễ trùng Thứ 7 hoặc Chủ nhật sẽ được nghỉ bù vào Thứ 6 trước hoặc Thứ 2 sau. Riêng range Tết Nguyên Đán không áp dụng bù thêm.

Danh sách Tết Nguyên Đán và Giỗ Tổ đã có sẵn cho **2024–2028**. Sau năm 2028, cần cập nhật thủ công trong hàm `vn_holidays()`.

## Cập nhật hàng ngày

Thêm vào crontab để tự động chạy mỗi sáng:

```bash
# Chạy lúc 9:00, Thứ 2 – Thứ 6, append vào file hiện có
0 9 * * 1-5 cd /path/to/sjc-gold-crawler && python sjc_gold_crawler.py --start 2025-01-01 --resume
```

## Thông tin kỹ thuật

Trang sjc.com.vn sử dụng ASP.NET WebForms, render bảng giá qua postback sau khi chọn ngày. DOM đã xác nhận tháng 3/2026:

- Ô nhập ngày: `id="datesearch"`, kiểu `text`, định dạng `DD/MM/YYYY`
- Nút tra cứu: `class="button-datesearch"`, text "Tra cứu"

Tốc độ crawl: khoảng **3 giây / ngày** → 300 ngày ≈ 15 phút.
