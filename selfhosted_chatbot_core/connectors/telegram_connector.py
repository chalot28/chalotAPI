import time
from typing import List, Optional
try:
    import requests  # nếu đã cài, dùng bình thường
except ModuleNotFoundError:
    from utils.requests_shim import requests  # fallback stdlib, không cần cài gì

from requests.adapters import HTTPAdapter, Retry

from .base import BaseConnector, Message

API_URL = "https://api.telegram.org/bot{token}/{method}"

def _build_session() -> requests.Session:
    s = requests.Session()
    # Retry cả lỗi kết nối/máy chủ và 429
    retries = Retry(
        total=4,                # tổng số retry
        backoff_factor=0.6,     # backoff: 0.6s, 1.2s, 1.8s, 2.4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods={"GET", "POST"},
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=50)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    # Tùy chọn: nếu bạn cần proxy, set ở đây:
    # s.proxies.update({"https": "http://127.0.0.1:8888"})
    return s

class TelegramConnector(BaseConnector):
    name = "telegram"

    def __init__(self, bot_token: str):
        self.token = bot_token
        self.offset: Optional[int] = None
        self.s = _build_session()

    def get_new_messages(self) -> List[Message]:
        # Long-polling nhẹ (timeout phía Telegram ~25s), nhưng timeout requests = 35s
        params = {"timeout": 25}
        if self.offset:
            params["offset"] = self.offset + 1

        try:
            r = self.s.get(
                API_URL.format(token=self.token, method="getUpdates"),
                params=params,
                timeout=35
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("result", []) if data.get("ok") else []

            msgs: List[Message] = []
            for upd in results:
                self.offset = max(self.offset or 0, upd.get("update_id", 0))
                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat = msg.get("chat", {})
                text = msg.get("text") or ""
                if not text:
                    continue
                msgs.append(Message(
                    thread_id=str(chat.get("id")),
                    sender_id=str(msg.get("from", {}).get("id")),
                    text=text
                ))
            return msgs
        except requests.exceptions.Timeout:
            # long-polling hết hạn là bình thường → không coi là lỗi
            return []
        except Exception:
            # Đừng ném lỗi để không làm sập vòng lặp
            return []

    def send_message(self, thread_id: str, text: str):
        payload = {
            "chat_id": thread_id,
            "text": text,
            "disable_web_page_preview": True
        }

        # Thử 1 lần nhanh, nếu timeout thì tự backoff thêm vài lần
        tries = 3
        delay = 1.0
        last_exc = None

        for i in range(tries):
            try:
                r = self.s.post(
                    API_URL.format(token=self.token, method="sendMessage"),
                    json=payload,
                    timeout=12   # ngắn hơn 30s để sớm retry
                )
                r.raise_for_status()
                return r.json()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
                last_exc = e
                time.sleep(delay)
                delay *= 1.8
                continue
            except Exception as e:
                # các lỗi khác trả về để logger phía trên in ra
                raise e
        # Sau khi đã retry vẫn fail → raise ReadTimeout để bot xử lý log nhưng không chết
        raise requests.exceptions.ReadTimeout(last_exc, request=None)

    def health_check(self) -> bool:
        try:
            r = self.s.get(
                API_URL.format(token=self.token, method="getMe"),
                timeout=8
            )
            return r.status_code == 200 and r.json().get("ok", False)
        except Exception:
            return False
# --- BEGIN REMINDER UPGRADE ---
import re
try:
    from ..reminders.scheduler import ReminderScheduler
    from ..reminders.service import handle_message, acknowledge_if_cycle
except Exception as _e:
    print("[telegram] reminder modules not available:", _e)
    ReminderScheduler = None

def _send_reminder(chat_id: str, text: str, meta: dict):
    try:
        send_message(chat_id, text)  # dùng hàm gửi sẵn có của connector
    except Exception as e:
        print("[telegram] failed to send reminder:", e)

_scheduler_instance = None
def start_reminder_scheduler():
    global _scheduler_instance
    if ReminderScheduler and _scheduler_instance is None:
        _scheduler_instance = ReminderScheduler(_send_reminder)
        _scheduler_instance.start()
        print("[telegram] ReminderScheduler started")

def on_incoming_text(user_id: str, chat_id: str, text: str):
    resp = handle_message(user_id, chat_id, text)
    if resp:
        send_message(chat_id, resp)
        return
    # Heuristic ack: nếu text chứa cycle key (tùy bạn cải tiến theo reply_to_message)
    m = re.search(r"(\w{8}-\w{4}-\w{4}-\w{4}-\w{12}@\d{12})", text)
    if m:
        acknowledge_if_cycle(text, m.group(1))
        return
# --- END REMINDER UPGRADE ---
