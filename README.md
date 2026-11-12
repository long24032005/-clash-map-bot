# Clash map bot

Bot tự động: lấy ảnh chụp team trong thư mục Google Drive → đọc số màn → đăng lên Discord kèm danh sách màn đã vượt. Chạy trên GitHub khoảng 10 phút/lần, không cần bật máy tính.

## Cách dùng hằng ngày

1. Chụp màn hình chọn team trong game.
2. Trên điện thoại: **Chia sẻ → Drive** → chọn thư mục **Clash map** → Tải lên.
3. Chờ khoảng 10–20 phút, ảnh sẽ lên Discord. Trên Drive, tên ảnh sẽ đổi thành:
   - `✅ 29-80 - ...` : đã đăng
   - `❌ ... - ...` : lỗi (không đọc được / màn cũ hơn / trùng màn), bot bỏ qua. Xóa ảnh đó đi là xong.

⚠️ Đừng đổi tên hay xóa các ảnh có dấu ✅ — bot dựa vào chúng để biết màn cuối cùng đã đăng.

---

## Cài đặt (làm 1 lần)

### Bước 1 — Lấy webhook Discord và link bài đăng
1. Chuột phải **kênh diễn đàn** chứa bài đăng (kênh cha, không phải bài đăng) → **Chỉnh sửa kênh** → **Tích hợp** → **Webhook** → **Webhook mới**.
2. Đặt tên (ví dụ `Clash map`) → **Sao chép URL Webhook**. Dán tạm vào Notepad.
3. Mở bài đăng muốn bot đăng vào → chuột phải tên bài đăng (trên điện thoại: nhấn giữ) → **Sao chép liên kết** (Copy Link). Dán tạm vào Notepad.
   (Nếu muốn bot đăng thẳng vào kênh thường thì bỏ qua bước 3 và không tạo secret `DISCORD_THREAD`.)

### Bước 2 — Tạo thư mục trên Google Drive
1. Vào https://drive.google.com → **Mới** → **Thư mục mới** → đặt tên `Clash map`.
2. Mở thư mục đó. Nhìn thanh địa chỉ: `https://drive.google.com/drive/folders/1AbCdEf...xyz`
3. Copy phần **sau `/folders/`** (ví dụ `1AbCdEf...xyz`) — đây là **ID thư mục**. Dán tạm vào Notepad.

### Bước 3 — Tạo "tài khoản robot" Google (service account)
1. Vào https://console.cloud.google.com, đăng nhập bằng **cùng tài khoản Google** với Drive. Nếu hỏi điều khoản → đồng ý.
2. **Tạo project**: bấm ô chọn project ở thanh trên cùng (cạnh logo Google Cloud) → **New Project** → tên `clash-map-bot` → **Create**. Đợi xong rồi bấm **Select project**.
3. **Bật Drive API**: gõ `Google Drive API` vào ô tìm kiếm trên cùng → bấm kết quả **Google Drive API** → **Enable**.
4. **Tạo service account**: gõ `Service accounts` vào ô tìm kiếm → mở **Service Accounts** → **+ Create service account**
   - Tên: `clash-bot` → **Create and continue** → bỏ qua phần quyền, bấm **Continue** → **Done**.
5. Bấm vào service account vừa tạo → copy **Email** của nó (dạng `clash-bot@clash-map-bot-xxxx.iam.gserviceaccount.com`), dán tạm vào Notepad.
6. Vẫn trong trang đó → tab **Keys** → **Add key** → **Create new key** → chọn **JSON** → **Create**. Một file `.json` sẽ được tải về máy.
   🔒 File này như mật khẩu — không gửi cho ai, không đăng lên đâu.

### Bước 4 — Chia sẻ thư mục Drive cho robot
1. Quay lại Google Drive → chuột phải thư mục **Clash map** → **Chia sẻ**.
2. Dán **email của service account** (bước 3.5) → chọn quyền **Người chỉnh sửa (Editor)** → bỏ tick "Thông báo" → **Chia sẻ**.

### Bước 5 — Đưa code lên GitHub
1. Vào https://github.com → dấu **+** góc trên phải → **New repository**.
2. Repository name: `clash-map-bot` → chọn **Public** → **Create repository**.
3. Ở trang repo trống, bấm link **uploading an existing file**.
4. Mở thư mục `clash-map-bot` trên máy, **chọn tất cả** bên trong (gồm cả thư mục `.github`) → kéo thả vào trang GitHub → bấm **Commit changes**.
5. Kiểm tra: trong repo phải thấy thư mục `.github`. Nếu không thấy, xem mục "Gặp lỗi" bên dưới.

### Bước 6 — Cất các "mật khẩu" vào GitHub Secrets
Trong repo: **Settings** → menu trái **Secrets and variables** → **Actions** → **New repository secret**. Tạo 4 cái (tên phải gõ đúng y hệt):

| Name | Secret (nội dung) |
|---|---|
| `DISCORD_WEBHOOK` | URL webhook ở bước 1.2 |
| `DISCORD_THREAD` | Link bài đăng ở bước 1.3 |
| `DRIVE_FOLDER_ID` | ID thư mục ở bước 2 |
| `GDRIVE_KEY` | Mở file `.json` ở bước 3.6 bằng **Notepad** → Ctrl+A, Ctrl+C → dán toàn bộ vào |

### Bước 7 — Chạy thử
1. Up 1–2 ảnh chụp team vào thư mục **Clash map** trên Drive.
2. Trong repo GitHub → tab **Actions**. Nếu có nút xanh **"I understand my workflows, go ahead and enable them"** → bấm.
3. Bấm **Clash map bot** (menu trái) → **Run workflow** → **Run workflow**.
4. Đợi 1–2 phút, tải lại trang. Dấu ✅ xanh = thành công → kiểm tra Discord và Drive.

Từ giờ bot tự chạy khoảng 10 phút/lần. Muốn đăng ngay thì làm lại bước 7.3.

---

## Gặp lỗi?

- **Dấu ❌ đỏ trong tab Actions**: bấm vào lần chạy đó → bấm **run** → xem dòng chữ đỏ.
  - `Thieu secret: ...` → làm lại bước 6, kiểm tra tên secret gõ đúng.
  - `HttpError 404` / `403` → chưa chia sẻ thư mục cho email robot (bước 4), hoặc sai ID thư mục, hoặc chưa bật Drive API (bước 3.3).
  - `HTTP Error 401/404` khi đăng Discord → URL webhook sai, webhook đã bị xóa, hoặc link bài đăng sai.
  - `HTTP Error 400` khi đăng Discord → webhook tạo ở kênh diễn đàn nhưng thiếu secret `DISCORD_THREAD`, hoặc bài đăng thuộc kênh khác với kênh tạo webhook.
- **Không thấy thư mục `.github` sau khi upload**: trong repo bấm **Add file → Create new file**, ô tên gõ `.github/workflows/chay-bot.yml`, mở file `chay-bot.yml` trên máy bằng Notepad, copy toàn bộ dán vào → **Commit changes**.
- **Bot ngừng chạy sau một thời gian dài không dùng**: GitHub tự tắt lịch chạy nếu repo không có hoạt động 60 ngày. Vào tab **Actions** → **Clash map bot** → bấm **Enable workflow**.
- **Ảnh đầu tiên** bot đăng chỉ ghi "📍 Đang ở màn X" (vì chưa có ảnh trước để so). Từ ảnh thứ 2 trở đi mới liệt kê màn đã vượt.
- Mỗi tầng tính 80 màn. Nếu game đổi số màn mỗi tầng, sửa `STAGES_PER_CHAPTER = 80` trong `bot.py`.
