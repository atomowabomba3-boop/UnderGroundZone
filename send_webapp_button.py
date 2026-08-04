#!/usr/bin/env python3
"""
send_webapp_button.py

Send an inline Web App button to a chat using BOT_TOKEN from environment.
Usage:
  python send_webapp_button.py <CHAT_ID>

Environment variables:
  BOT_TOKEN   - required (set this in Railway project variables)
  WEBAPP_URL  - optional, defaults to https://web-production-23ff3.up.railway.app

The script uses the Telegram sendMessage API with an inline_keyboard and web_app.url
so clicking the button should open the Web App inside the Telegram client and provide initData.
"""
import os
import sys
import json
import urllib.request

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://web-production-23ff3.up.railway.app')

if len(sys.argv) < 2:
    print("Usage: python send_webapp_button.py <CHAT_ID>")
    sys.exit(2)

CHAT_ID = sys.argv[1]

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not set in environment. Set BOT_TOKEN in Railway project variables.")
    sys.exit(1)

payload = {
    "chat_id": CHAT_ID,
    "text": "Otwórz Web App",
    "reply_markup": {
        "inline_keyboard": [
            [
                {"text": "Otwórz", "web_app": {"url": WEBAPP_URL}}
            ]
        ]
    }
}

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode('utf-8')
        print('Response from Telegram:')
        print(body)
except Exception as e:
    print('Request failed: ', e)
    sys.exit(1)
