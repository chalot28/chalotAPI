# Self-Hosted Chatbot Core (Safe & Compliant)

> Đây là **bộ khung chatbot tự lưu trữ** bằng Python với giao diện quản lý web (Flask), tách cấu hình ra file JSON, có log chi tiết. 
> **Không** bao gồm bất kỳ mã nào dùng API nội bộ hay nhằm vượt qua giới hạn nền tảng. 
> Bạn có thể cắm các connector **hợp lệ** (Telegram, Facebook Graph API chính thức, v.v.) vào.

## Tính năng
- Cấu trúc module rõ ràng: `connectors/`, `config/`, `web/`, `utils/`
- Giao diện quản lý (Flask): xem log, sửa `settings.json`, `replies.json`, `credentials.json`
- Logic trả lời theo kịch bản (rule-based), dễ thay thế bằng NLP/LLM
- Lịch canary/health-check bằng APScheduler
- Log ra console + file `logs/bot.log` (hiển thị rõ trên PowerShell)

## Cài đặt
```bash
python -m venv .venv
. .venv/Scripts/activate    # Windows PowerShell
pip install -r requirements.txt
```

## Cấu hình
- `config/settings.json`:
  - `connector`: `mock` | `telegram` | `facebook_graph_api`
  - `poll_interval_seconds`: chu kỳ quét tin
  - `admin_password`: mật khẩu đăng nhập giao diện quản lý
- `config/credentials.json`:
  - Telegram: `bot_token`
  - Facebook Graph API: `page_access_token`, `page_id` (cần App Review hợp lệ)
- `config/replies.json`: kịch bản trả lời

## Chạy bot (console)
```bash
python bot.py
```
Quan sát log trên PowerShell, ví dụ:
```
[2025-09-06 20:15:00] [INFO] 🚀 Bot khởi động...
[2025-09-06 20:15:00] [INFO] ✅ Connector 'mock' sẵn sàng.
[2025-09-06 20:15:03] [INFO] 💬 Tin nhắn mới từ u1 (u1): hello
[2025-09-06 20:15:03] [INFO] 📤 Đã trả lời u1: Chào bạn! Mình có thể hỗ trợ gì hôm nay?
```

## Giao diện quản lý
```bash
# Chạy web UI
set FLASK_APP=web/app.py
python -m flask run
# Mở http://127.0.0.1:5000 (mật khẩu: admin_password trong settings.json)
```

## Connector
- `mock_connector.py`: mô phỏng inbox để bạn test UI/logic
- `telegram_connector.py`: **hợp lệ** dùng Telegram Bot API
- `facebook_graph_api.py`: placeholder **hợp lệ** dùng Graph API chính thức (khuyến nghị dùng Webhook để nhận tin)

> Bạn có thể viết connector khác bằng cách kế thừa `connectors/base.py`.

## Lưu ý pháp lý
- Dự án **không** cung cấp phương thức sử dụng API nội bộ hoặc vượt qua kiểm duyệt nền tảng.
- Khi tích hợp Facebook, hãy dùng **Graph API chính thức** và tuân thủ điều khoản của Meta.

## Tùy biến
- Thay `BotLogic` bằng module AI.
- Tạo trang quản trị nâng cao: xem hội thoại, bật/tắt bot theo thread, v.v.

Chúc bạn vận hành trơn tru! 🎯
