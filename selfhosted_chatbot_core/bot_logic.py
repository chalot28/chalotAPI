import re
import unicodedata
from typing import Dict, Any, List, Optional

def _normalize(s: str) -> str:
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # bỏ dấu
    s = re.sub(r"\s+", " ", s)
    return s

def _tokenize(s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", _normalize(s)))

class BotLogic:
    """So khớp kịch bản theo từ khóa (bỏ dấu, không phân biệt hoa thường)."""
    def __init__(self, replies_config: Dict[str, Any]):
        self.intents: List[Dict[str, Any]] = replies_config.get("intents", [])
        self.fallback: str = replies_config.get("fallback", "Cám ơn bạn đã nhắn tin!")

    def find_match(self, text: str) -> Optional[str]:
        user_tokens = _tokenize(text or "")
        for intent in self.intents:
            kws = intent.get("match", [])
            # Khớp nếu bất kỳ keyword có đầy đủ từ cấu thành xuất hiện trong user_tokens
            for kw in kws:
                kw_tokens = _tokenize(kw)
                if kw_tokens and kw_tokens.issubset(user_tokens):
                    return intent.get("reply", self.fallback)
        return None

    # Giữ lại cho tương thích cũ (không dùng nếu đã gọi find_match)
    def make_reply(self, text: str) -> str:
        matched = self.find_match(text)
        return matched if matched is not None else self.fallback
