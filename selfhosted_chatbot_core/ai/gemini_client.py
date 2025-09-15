import requests

def generate(prompt: str, api_url: str, model: str, api_key: str, system_prompt: str = "") -> str:
    """Gọi Gemini generateContent API"""
    if not (api_url and model and api_key):
        return "(AI chưa cấu hình đầy đủ: thiếu api_url/model/api_key)"

    endpoint = f"{api_url.rstrip('/')}/{model}:generateContent?key={api_key}"
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]
            }
        ]
    }
    try:
        r = requests.post(endpoint, json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        return (
            data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "Xin lỗi, hiện chưa có phản hồi phù hợp.")
        )
    except Exception as e:
        return f"(Lỗi gọi Gemini: {e})"
