import os, requests

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_message(msg):
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(BOT_TOKEN)
    params = {'chat_id': CHAT_ID, 'text': msg}
    requests.get(url, params=params)