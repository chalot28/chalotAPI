from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class Message:
    def __init__(self, thread_id: str, sender_id: str, text: str):
        self.thread_id = thread_id
        self.sender_id = sender_id
        self.text = text

class BaseConnector(ABC):
    name: str = "base"

    @abstractmethod
    def get_new_messages(self) -> List[Message]:
        """Fetch new messages since last poll."""
        raise NotImplementedError

    @abstractmethod
    def send_message(self, thread_id: str, text: str) -> Any:
        """Send a text message to a thread/user."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if connector is healthy/authenticated."""
        raise NotImplementedError

    def canary(self, text: str) -> bool:
        """Optional canary test hook."""
        return True
