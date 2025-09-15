import os
import json
import time

# APScheduler là tùy chọn — để chạy không cần lib ngoài
try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:
    BackgroundScheduler = None

from utils.logger import setup_logger
from bot_logic import BotLogic
from connectors.base import BaseConnector
from connectors.mock_connector import MockConnector
from connectors.telegram_connector import TelegramConnector
from connectors.facebook_graph_api import FacebookGraphAPIConnector
from ai.gemini_client import generate as gemini_generate  # ✨ thêm Gemini client

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
LOG = setup_logger("bot")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ✨ helper lấy config AI
def get_ai_config():
    settings = load_json(os.path.join(CONFIG_DIR, "settings.json"))
    creds = load_json(os.path.join(CONFIG_DIR, "credentials.json"))
    ai = settings.get("ai", {})
    return {
        "enabled": ai.get("enabled", True),
        "provider": ai.get("provider", "gemini"),
        "model": ai.get("model", "gemini-1.5-flash-latest"),
        "api_url": ai.get("api_url", "https://generativelanguage.googleapis.com/v1beta/models"),
        "api_key": creds.get("gemini", {}).get("api_key", ""),
        "system_prompt": ai.get("system_prompt", "Bạn là trợ lý thân thiện. Trả lời ngắn gọn, rõ ràng, tiếng Việt.")
    }

def make_connector(settings, credentials) -> BaseConnector:
    choice = settings.get("connector", "mock").lower()
    if choice == "telegram":
        token = credentials.get("telegram", {}).get("bot_token", "")
        return TelegramConnector(token)
    elif choice == "facebook_graph_api":
        fb = credentials.get("facebook_graph_api", {})
        return FacebookGraphAPIConnector(fb.get("page_access_token",""), fb.get("page_id",""))
    else:
        return MockConnector()

class BotRunner:
    def __init__(self):
        self.settings = load_json(os.path.join(CONFIG_DIR, "settings.json"))
        self.replies = load_json(os.path.join(CONFIG_DIR, "replies.json"))
        self.logic = BotLogic(self.replies)
        self.connector = make_connector(self.settings, load_json(os.path.join(CONFIG_DIR, "credentials.json")))
        # Scheduler là tùy chọn
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None
        self._stop = False

    def start(self):
        LOG.info("🚀 Bot khởi động...")
        if self.connector.health_check():
            LOG.info(f"✅ Connector '{self.connector.name}' sẵn sàng.")
        else:
            LOG.warning(f"⚠️ Connector '{self.connector.name}' chưa sẵn sàng. Vẫn tiếp tục và thử lại...")

        # Khởi động Reminder Scheduler cho Telegram (nếu dùng Telegram)
        if isinstance(self.connector, TelegramConnector):
            try:
                # import tuyệt đối để phù hợp cách chạy `py bot.py`
                from connectors.telegram_connector import start_reminder_scheduler
                start_reminder_scheduler()
            except Exception as _e:
                LOG.warning(f"[bot] Không thể start reminder scheduler: {_e}")

        # Canary job (nếu có APScheduler)
        if self.settings.get("canary_enabled", True) and self.scheduler:
            interval = int(self.settings.get("canary_interval_minutes", 10))
            self.scheduler.add_job(self.run_canary, "interval", minutes=interval, id="canary")
            self.scheduler.start()
        elif not BackgroundScheduler:
            LOG.info("[bot] APScheduler không có — bỏ qua các job APScheduler.")

        self.loop()

    def stop(self):
        self._stop = True
        if self.scheduler:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass
        LOG.info("🛑 Dừng bot.")

    def loop(self):
        poll = int(self.settings.get("poll_interval_seconds", 3))
        while not self._stop:
            try:
                msgs = self.connector.get_new_messages()
                for m in msgs:
                    LOG.info(f"💬 Tin nhắn mới từ {m.sender_id} ({m.thread_id}): {m.text}")

                    # ✨ Kịch bản trước → fallback Gemini
                    scenario_reply = getattr(self.logic, "find_match", self.logic.make_reply)(m.text)
                    if scenario_reply is not None:
                        reply = scenario_reply
                        LOG.debug(f"Decision: SCENARIO -> {reply!r}")
                    else:
                        ai_cfg = get_ai_config()
                        if ai_cfg.get("enabled"):
                            LOG.debug(f"Decision: GEMINI with prompt={m.text!r}")
                            reply = gemini_generate(
                                prompt=m.text or "",
                                api_url=ai_cfg["api_url"],
                                model=ai_cfg["model"],
                                api_key=ai_cfg["api_key"],
                                system_prompt=ai_cfg.get("system_prompt","")
                            )
                        else:
                            reply = self.logic.fallback
                            LOG.debug("Decision: FALLBACK")

                    self.connector.send_message(m.thread_id, reply)
                    LOG.info(f"📤 Đã trả lời {m.thread_id}: {reply}")
            except Exception as e:
                LOG.exception(f"Lỗi vòng lặp: {e}")
            time.sleep(poll)

    def run_canary(self):
        try:
            ok = self.connector.health_check()
            LOG.info(f"🔎 Health-check: {'OK' if ok else 'FAIL'}")
        except Exception as e:
            LOG.exception(f"Health-check exception: {e}")

if __name__ == "__main__":
    BotRunner().start()
