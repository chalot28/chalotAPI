import os, json, urllib.request

PANTRY_HOST = os.environ.get("PANTRY_HOST", "getpantry.cloud")
BIN_ID = os.environ.get("PANTRY_BIN_ID")  # must be set
TIMEOUT = 10

def _bin_url():
    if not BIN_ID:
        raise RuntimeError("PANTRY_BIN_ID is not set in environment")
    return f"https://{PANTRY_HOST}/apiv1/pantry/{BIN_ID}"

def _headers():
    return {"Content-Type": "application/json"}

def _get_json():
    req = urllib.request.Request(_bin_url(), headers=_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read().decode("utf-8")
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}
    data.setdefault("reminders", {})
    data.setdefault("cycles", {})
    return data

def _put_json(data: dict):
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(_bin_url(), headers=_headers(), data=payload, method="PUT")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        _ = r.read()
    return True

def load_all():
    return _get_json()

def save_all(data: dict):
    return _put_json(data)

def upsert_reminder(reminder: dict):
    data = _get_json()
    rid = reminder["id"]
    data["reminders"][rid] = reminder
    _put_json(data)
    return True

def delete_reminder(reminder_id: str):
    data = _get_json()
    if reminder_id in data["reminders"]:
        del data["reminders"][reminder_id]
    keys_to_del = [k for k in data.get("cycles", {}).keys() if k.startswith(reminder_id + "@")]
    for k in keys_to_del:
        del data["cycles"][k]
    _put_json(data)
    return True

def upsert_cycle(key: str, item: dict):
    data = _get_json()
    data["cycles"][key] = item
    _put_json(data)

def delete_cycle(key: str):
    data = _get_json()
    if key in data.get("cycles", {}):
        del data["cycles"][key]
        _put_json(data)

def bulk_update(changes):
    data = _get_json()
    newdata = changes(data) if callable(changes) else data
    _put_json(newdata)
    return True
