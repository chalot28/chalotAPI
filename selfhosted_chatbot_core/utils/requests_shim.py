# utils/requests_shim.py
# "Giả lập" giao diện tối thiểu của requests.get/post bằng urllib (stdlib)

import urllib.request, urllib.parse, json, ssl

class _Resp:
    def __init__(self, data, code=200):
        self._data = data
        self.status_code = code
        self.text = json.dumps(data, ensure_ascii=False)

    def json(self):
        return self._data

class _RequestsShim:
    def __init__(self):
        self._ctx = ssl.create_default_context()

    def get(self, url, params=None, headers=None, timeout=15):
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
            body = r.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {"ok": False, "raw": body}
            return _Resp(data, r.getcode())

    def post(self, url, data=None, json=None, headers=None, timeout=15):
        if json is not None:
            payload = json.dumps(json).encode("utf-8")
            hdrs = {"Content-Type": "application/json"}
        else:
            if isinstance(data, dict):
                payload = urllib.parse.urlencode(data).encode("utf-8")
                hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
            elif isinstance(data, (bytes, bytearray)):
                payload = data
                hdrs = {}
            else:
                payload = (data or "").encode("utf-8")
                hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, data=payload, headers=hdrs)
        with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
            body = r.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {"ok": False, "raw": body}
            return _Resp(data, r.getcode())

# export "requests" biến tương thích
requests = _RequestsShim()
