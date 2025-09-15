import re, uuid
from ..utils import pantry
from .scheduler import now_local

TIME_PAT = r"(\d{1,2}(?::\d{2})?)(?:\s*h?)?"
DATE_PAT = r"(\d{1,2})\s*(?:th|/|-)\s*(\d{1,2})"
DAILY_PAT = r"(hằng\s*ngày|mỗi\s*ngày|every\s*day)"
TEXT_PAT = r"\"([^\"]+)\"|:([\s\S]+)$"

def _norm_time(s: str) -> str:
    s = s.replace("h", ":").replace("H", ":")
    if ":" not in s:
        return f"{int(s):02d}:00"
    hh, mm = s.split(":")[0:2]
    return f"{int(hh):02d}:{int(mm):02d}"

def _parse(msg: str):
    m = re.search(r"tắt\s+nhắc\s*nhở\s*lúc\s*"+TIME_PAT, msg, flags=re.I)
    if m:
        return {"action":"cancel","time": _norm_time(m.group(1))}
    m = re.search(r"nhắc(?:\s*nhở)?(?:\s+vào|\s+lúc)?\s*"+TIME_PAT+r"(?:\s+"+DATE_PAT+")?(?:\s*("+DAILY_PAT+"))?.*?(?:với\s*nội\s*dung\s*"+TEXT_PAT+"|"+TEXT_PAT+")", msg, flags=re.I)
    if not m:
        m = re.search(r"nhắc(?:\s*nhở)?\s*"+TIME_PAT+r"(?:\s+"+DATE_PAT+")?(?:\s*("+DAILY_PAT+"))?\s*"+TEXT_PAT, msg, flags=re.I)
    if m:
        time_s = _norm_time(m.group(1))
        day = m.group(2); month = m.group(3)
        daily = (m.group(4) or "").strip() if len(m.groups())>=4 else ""
        text = (m.group(5) or m.group(6) or "").strip()
        if text.startswith(":"):
            text = text[1:].strip()
        date_iso = None
        if day and month:
            y = now_local().year
            date_iso = f"{y:04d}-{int(month):02d}-{int(day):02d}"
        repeat = "daily" if daily else ("once" if date_iso else "once_today")
        return {"action":"create","time": time_s, "date": date_iso, "repeat": repeat, "text": text}
    return {"action":"none"}

def handle_message(user_id: str, chat_id: str, text: str) -> str:
    parsed = _parse(text)
    if parsed["action"] == "cancel":
        t = parsed["time"]
        def changer(data):
            rems = data.get("reminders", {})
            to_del = [rid for rid, r in rems.items() if r.get("platform")=="telegram" and r.get("user_id")==user_id and r.get("time")==t]
            for rid in to_del:
                del rems[rid]
            cycles = data.get("cycles", {})
            for k in list(cycles.keys()):
                if any(k.startswith(rid+"@") for rid in to_del):
                    del cycles[k]
            data["reminders"] = rems; data["cycles"] = cycles
            return data
        pantry.bulk_update(changer)
        return f"Đã tắt mọi nhắc nhở lúc {t} của bạn."
    elif parsed["action"] == "create":
        rid = str(uuid.uuid4())
        repeat = parsed["repeat"]
        date_iso = parsed.get("date")
        if repeat == "once_today":
            date_iso = now_local().date().isoformat()
            repeat = "once"
        reminder = {
            "id": rid,
            "user_id": user_id,
            "platform": "telegram",
            "chat_id": chat_id,
            "time": parsed["time"],
            "date": date_iso,
            "repeat": repeat,
            "text": parsed["text"] or "8h rồi đi chơi thôi",
            "created_at": now_local().isoformat(),
            "last_fired": None,
            "active_cycle_key": None,
            "tz": "Asia/Ho_Chi_Minh"
        }
        pantry.upsert_reminder(reminder)
        when = f"lúc {parsed['time']}"
        if date_iso:
            when += f" ngày {date_iso}"
        if repeat == "daily":
            when += " (lặp mỗi ngày)"
        return f"Đã tạo nhắc nhở {when}: “{reminder['text']}”"
    else:
        return ""

def acknowledge_if_cycle(text_reply: str, cycle_key: str):
    def changer(data):
        if cycle_key in data.get("cycles", {}):
            c = data["cycles"][cycle_key]
            c["ack"] = True
            c["ack_text"] = text_reply
        return data
    pantry.bulk_update(changer)
