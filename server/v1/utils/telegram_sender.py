import requests
from flask import current_app


def send_message(msg):
    if not current_app.config.get("BOT_TOKEN") or not current_app.config.get("CHAT_ID"):
        return

    url = f"https://api.telegram.org/bot{current_app.config['BOT_TOKEN']}/sendMessage"
    params = {"chat_id": current_app.config["CHAT_ID"], "text": msg}
    requests.get(url, params=params)
