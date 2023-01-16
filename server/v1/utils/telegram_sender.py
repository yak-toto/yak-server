import requests
from flask import current_app


def send_message(msg):
    url = f"https://api.telegram.org/bot{current_app.config['BOT_TOKEN']}/sendMessage"
    params = {"chat_id": current_app.config["CHAT_ID"], "text": msg}
    requests.get(url, params=params)
