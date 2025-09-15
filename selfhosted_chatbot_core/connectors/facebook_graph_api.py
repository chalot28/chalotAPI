import requests
from typing import List
from .base import BaseConnector, Message

# NOTE: This connector uses the official Graph API and requires proper permissions and webhook setup.
# It is provided as a placeholder for compliant integrations.
# Inbound messages typically arrive via webhook callbacks; to simplify, this class provides a polling endpoint
# for demonstration (Graph API does not provide simple polling for messages in production).

class FacebookGraphAPIConnector(BaseConnector):
    name = "facebook_graph_api"

    def __init__(self, page_access_token: str, page_id: str):
        self.token = page_access_token
        self.page_id = page_id
        self.after_cursor = None

    def get_new_messages(self) -> List[Message]:
        # Placeholder: In reality, use Webhooks to receive messages.
        # Here we return an empty list to avoid misleading behavior.
        return []

    def send_message(self, thread_id: str, text: str):
        url = f"https://graph.facebook.com/v20.0/me/messages"
        params = {"access_token": self.token}
        payload = {"recipient": {"id": thread_id}, "message": {"text": text}}
        r = requests.post(url, params=params, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    def health_check(self) -> bool:
        try:
            url = f"https://graph.facebook.com/v20.0/{self.page_id}"
            r = requests.get(url, params={"access_token": self.token}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False
