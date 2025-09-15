import time
from typing import List
from .base import BaseConnector, Message

class MockConnector(BaseConnector):
    name = "mock"

    def __init__(self):
        self._inbox = [
            Message(thread_id="u1", sender_id="u1", text="hello"),
            Message(thread_id="u2", sender_id="u2", text="giá bao nhiêu"),
        ]
        self._sent = []
        self._last_idx = 0

    def get_new_messages(self) -> List[Message]:
        time.sleep(0.01)
        # Simulate reading only new messages
        new = self._inbox[self._last_idx:]
        self._last_idx = len(self._inbox)
        return new

    def send_message(self, thread_id: str, text: str):
        self._sent.append((thread_id, text))
        return {"ok": True, "thread_id": thread_id, "text": text}

    def health_check(self) -> bool:
        return True

    # Helpers for tests / UI
    def inject_message(self, thread_id: str, text: str, sender_id: str = None):
        self._inbox.append(Message(thread_id=thread_id, sender_id=sender_id or thread_id, text=text))
