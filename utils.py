from datetime import datetime

import requests
from flask import current_app


def parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def push_webhook_message(message: str):
    webhook_url = current_app.config.get("GOOGLE_CHAT_WEBHOOK_URL", "")
    if not webhook_url:
        return False
    try:
        requests.post(webhook_url, json={"text": message}, timeout=5)
        return True
    except Exception:
        return False
