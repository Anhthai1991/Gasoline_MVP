# 🤖 Hướng Dẫn Tự Động Hóa Cập Nhật Giá Xăng Dầu

## 📋 Tổng Quan

Repo này đã được cấu hình với GitHub Actions để **tự động cập nhật giá xăng dầu PVOIL hàng ngày**. Workflow sẽ:
- ✅ Chạy script `update_pvoil_prices.py` tự động
- ✅ Commit và push dữ liệu mới lên repo
- ✅ Không cần can thiệp thủ công

---

## ⚙️ Cấu Hình Workflow Hiện Tại

### 📁 File: `.github/workflows/autoupdate.yml`

**Lịch chạy:**
- 🕐 **Hàng ngày lúc 1:00 AM UTC** (8:00 AM giờ Việt Nam)
- 🔧 Có thể chạy thủ công từ tab Actions

**Các bước thực hiện:**
1. **Checkout repository** - Lấy code mới nhất
2. **Setup Python 3.x** - Cài đặt môi trường Python
3. **Install dependencies** - Cài đặt các thư viện cần thiết:
   - `requests` - Gọi API/web scraping
   - `beautifulsoup4` - Parse HTML
   - `pandas` - Xử lý dữ liệu CSV
4. **Run update script** - Chạy `update_pvoil_prices.py`
5. **Commit & push** - Tự động commit và push nếu có thay đổi

---

## 🔐 Xác Thực & Quyền Truy Cập

### ✅ ĐÃ CẤU HÌNH

Workflow đã được cấu hình đầy đủ với:

```yaml
permissions:
  contents: write  # Cho phép workflow commit và push
```

Và sử dụng `GITHUB_TOKEN` mặc định:

```yaml
- name: Checkout repository
  uses: actions/checkout@v3
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

### 🎯 KHÔNG CẦN THIẾT LẬP TOKEN THỦ CÔNG

GitHub Actions tự động cung cấp `GITHUB_TOKEN` với đầy đủ quyền để:
- ✅ Clone repository
- ✅ Commit changes
- ✅ Push to main branch

**Lưu ý:** `GITHUB_TOKEN` được tạo tự động cho mỗi workflow run và hết hạn sau khi workflow kết thúc.

---

## 🚀 Cách Sử Dụng

### 1️⃣ Chạy Tự Động (Đã Cấu Hình)
Workflow sẽ tự động chạy hàng ngày lúc 8:00 AM (giờ VN). Không cần làm gì cả!

### 2️⃣ Chạy Thủ Công

1. Vào tab **[Actions](https://github.com/Anhthai1991/Fuel-VN-price/actions)**
2. Chọn workflow **"Auto Update Fuel Prices"**
3. Click **"Run workflow"** dropdown
4. Click nút **"Run workflow"** màu xanh

### 3️⃣ Xem Lịch Sử Chạy

Tại tab Actions, bạn có thể:
- 📊 Xem các lần chạy trước đó
- ✅ Kiểm tra trạng thái (success/fail)
- 📝 Xem logs chi tiết

---

## 📂 Cấu Trúc Files

```
Fuel-VN-price/
├── .github/
│   └── workflows/
│       └── autoupdate.yml          # Workflow tự động hóa
├── update_pvoil_prices.py          # Script cập nhật dữ liệu
├── pvoil_gasoline_prices_full.csv  # File dữ liệu CSV
├── index.html                       # Giao diện web
└── AUTOMATION_GUIDE.md             # Tài liệu này
```

---

## 🔧 Tùy Chỉnh Lịch Chạy

Để thay đổi tần suất chạy, sửa file `.github/workflows/autoupdate.yml`:

```yaml
schedule:
  - cron: '0 1 * * *'  # Hàng ngày lúc 1:00 AM UTC
```

**Ví dụ cron expressions:**
- `'0 */6 * * *'` - Chạy mỗi 6 giờ
- `'0 0 * * *'` - Chạy lúc 12:00 AM UTC (7:00 AM VN)
- `'0 0 * * 1'` - Chạy mỗi thứ Hai
- `'0 0 1 * *'` - Chạy ngày đầu tiên mỗi tháng

**Tool tạo cron:** https://crontab.guru/

---

## 🛠️ Troubleshooting

### ❌ Workflow không chạy?

1. **Kiểm tra tab Actions có bật không:**
   - Vào Settings → Actions → General
   - Đảm bảo "Allow all actions" được chọn

2. **Kiểm tra permissions:**
   - Settings → Actions → General → Workflow permissions
   - Chọn "Read and write permissions"

3. **Kiểm tra branch protection:**
   - Settings → Branches
   - Nếu có protection rules, cần allow GitHub Actions to push

### ⚠️ Workflow fail?

1. Vào tab **Actions** → Click vào workflow run bị fail
2. Xem logs để tìm lỗi
3. Các lỗi thường gặp:
   - **Dependencies missing:** Cần cập nhật `requirements.txt`
   - **Website changed:** Script cần update để parse HTML mới
   - **Rate limiting:** Thêm delay/retry trong script

### 📝 Không có commit mới?

- Workflow chỉ commit khi có thay đổi dữ liệu
- Nếu giá không đổi, sẽ không có commit mới (đây là hành vi mong muốn)

---

## 📊 Monitoring

### Cách theo dõi workflow:

1. **Email notifications:**
   - GitHub sẽ gửi email nếu workflow fail
   - Settings → Notifications → Actions

2. **Badges (Optional):**
   Thêm vào README.md:
   ```markdown
   ![Auto Update](https://github.com/Anhthai1991/Fuel-VN-price/actions/workflows/autoupdate.yml/badge.svg)
   ```

---

## 🎉 Kết Luận

✅ **Workflow đã được cấu hình đầy đủ và sẵn sàng hoạt động!**

Các cải tiến đã thực hiện:
- ✅ Sửa tên script từ `update_prices.py` → `update_pvoil_prices.py`
- ✅ Thay đổi lịch chạy: mỗi 7 ngày → **hàng ngày**
- ✅ Thêm `permissions: contents: write`
- ✅ Thêm `GITHUB_TOKEN` trong checkout
- ✅ Cài đặt dependencies trực tiếp
- ✅ Cải thiện commit message với timestamp

**Không cần cấu hình thêm gì nữa!** 🎊

---

## 📚 Tài Liệu Tham Khảo

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cron Schedule Syntax](https://crontab.guru/)
- [GitHub Token Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)

---

**Cập nhật lần cuối:** 03/11/2025
**Người tạo:** Comet Assistant 🤖
