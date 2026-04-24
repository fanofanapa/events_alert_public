import os

from dotenv import load_dotenv


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

COOKIES_FILE = "cookies.txt"
OUTPUT_FILE = "activities.json"
KNOWN_IDS_FILE = "known_ids.json"

API_BASE_URL = "https://www.gate.com/api/web/v1/welfare-center/activityList"

TYPE_IDS = [1, 4, 12, 14, 17, 213, 1066]

API_PARAMS_BASE = {
    "sub_website_id": 0,
    "status": "ongoing",
    "page_size": 9,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.gate.com/ru/rewards_hub/activity-center-1-ongoing",
    "csrftoken": "1",
    "sub_website_id": "0",
    "Alt-Used": "www.gate.com",
    "Connection": "keep-alive",
}

POLLING_INTERVAL = 300
REQUEST_DELAY = 2
TYPE_DELAY = 2
TG_MSG_SEND_DELAY = 2
TG_CHANNEL_URL = os.getenv("TG_CHANNEL_URL")
TG_POST_DESC = os.getenv("G_POST_DESC")