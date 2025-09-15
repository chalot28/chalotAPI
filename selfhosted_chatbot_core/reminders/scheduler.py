import threading, time, datetime, json, os
from typing import Callable, Dict, Any
from ..utils import pantry

TZ_OFFSET_MINUTES = 7*60  # UTC+7

def now_local():
    return datetime.datetime.utcnow() + datetime.timedelta(minutes=TZ_OFFSET_MINUTES)

def parse_hhmm(s: str) -> datetime.time:
    parts = s.split(":")
    hh = int(parts[0])
    mm = int(parts[1]) if len(parts) > 1 else 0
    return datetime.time(hour=hh, minute=mm)

class ReminderScheduler:
    def __init__(self, send_func: Callable[[str, str, Dict[str, Any]], None]):
        self._send = send_func
        self._stop = threading.Event()
        self._thr = None

    def start(self):
        if self._thr and self._thr.is_alive():
            return
        self._stop.clear()
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()

    def stop(self):
        self._stop.set()
        if self._thr:
            self._thr.join(timeout=1.0)

    def _run(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                print("[scheduler] error:", e)
            time.sleep(30)

    def _tick(self):
        data = pantry.load_all()
        reminders = data.get("reminders", {})
        cycles = data.get("cycles", {})

        now = now_local()

        to_delete = []
        for rid, r in list(reminders.items()):
            t = parse_hhmm(r.get("time", "08:00"))
            date_str = r.get("date")
            repeat = r.get("repeat", "once")
            last_fired = r.get("last_fired")
            chat_id = r.get("chat_id")

            if date_str:
                y, m, d = [int(x) for x in date_str.split("-")]
                target_day = datetime.date(y, m, d)
            else:
                target_day = now.date()

            target_dt = datetime.datetime.combine(target_day, t)

            if now >= target_dt and (now - target_dt).total_seconds() <= 60:
                cycle_key = f"{rid}@{target_dt.strftime('%Y%m%d%H%M')}"
                if cycle_key not in cycles:
                    msg = self._render_template(1, r.get("text", ""))
                    self._send(chat_id, msg, {"reminder_id": rid, "step": 1, "cycle_key": cycle_key})
                    cycles[cycle_key] = {"reminder_id": rid, "chat_id": chat_id, "step": 1, "t0": target_dt.isoformat()}
                    reminders[rid]["active_cycle_key"] = cycle_key
                    reminders[rid]["last_fired"] = now.date().isoformat()

            if repeat == "once" and last_fired:
                lf = datetime.date.fromisoformat(last_fired)
                base_day = datetime.date.fromisoformat(date_str) if date_str else now.date()
                if lf >= base_day:
                    to_delete.append(rid)

        for ckey, c in list(cycles.items()):
            rid = c["reminder_id"]
            r = reminders.get(rid)
            if not r:
                del cycles[ckey]
                continue
            if c.get("ack"):
                t0 = datetime.datetime.fromisoformat(c["t0"])
                if (now - t0).total_seconds() >= 1800:
                    del cycles[ckey]
                continue
            t0 = datetime.datetime.fromisoformat(c["t0"])
            dt = now - t0
            if c.get("step", 1) == 1 and dt.total_seconds() >= 600:
                msg = self._render_template(2, r.get("text", ""))
                self._send(r["chat_id"], msg, {"reminder_id": rid, "step": 2, "cycle_key": ckey})
                c["step"] = 2
            elif c.get("step") == 2 and dt.total_seconds() >= 1200:
                msg = self._render_template(3, r.get("text", ""))
                self._send(r["chat_id"], msg, {"reminder_id": rid, "step": 3, "cycle_key": ckey})
                c["step"] = 3
                c["done"] = True
                if (now - t0).total_seconds() >= 1800:
                    del cycles[ckey]

        for rid in to_delete:
            if rid in reminders:
                del reminders[rid]

        pantry.save_all({"reminders": reminders, "cycles": cycles})

    def _render_template(self, step: int, text: str) -> str:
        base = os.path.dirname(os.path.dirname(__file__))
        cfg = os.path.join(base, "config")
        fname = {1:"reminder_msg1.json", 2:"reminder_msg2.json", 3:"reminder_msg3.json"}.get(step, "reminder_msg1.json")
        try:
            with open(os.path.join(cfg, fname), "r", encoding="utf-8") as f:
                tpl = json.load(f).get("template", "{{text}}")
        except Exception:
            tpl = "{{text}}"
        return tpl.replace("{{text}}", text)
