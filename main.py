#!/usr/bin/env python3

import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from config import (
    COOKIES_FILE,
    KNOWN_IDS_FILE,
    OUTPUT_FILE,
    POLLING_INTERVAL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TG_MSG_SEND_DELAY,
    TYPE_IDS,
    TG_CHANNEL_URL,
    TG_POST_DESC
)
from llm_summary.qwen3_coder_next import get_summary_from_url
from parser import GateParser, load_netscape_cookies


TG_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def load_known_ids() -> set[str]:
    path = Path(KNOWN_IDS_FILE)

    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as file:
        return set(json.load(file))


def save_known_ids(ids: set[str]) -> None:
    with open(KNOWN_IDS_FILE, "w", encoding="utf-8") as file:
        json.dump(sorted(ids), file, ensure_ascii=False, indent=2)


def json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def save_activities(activities: list[dict[str, Any]]) -> None:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(activities, file, ensure_ascii=False, indent=2, default=json_default)


def send_telegram_message(text: str, photo_url: str | None = None) -> bool:
    if photo_url:
        endpoint = f"{TG_API_URL}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": photo_url,
            "caption": text,
            "parse_mode": "HTML",
        }
    else:
        endpoint = f"{TG_API_URL}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }

    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as error:
        description = "no details"

        if error.response is not None:
            try:
                description = error.response.json().get("description", description)
            except ValueError:
                description = error.response.text or description

        print(f"❌ Telegram API error: {description}")
        return False
    except requests.RequestException as error:
        print(f"❌ Telegram request failed: {error}")
        return False


def format_activity_message(activity: dict[str, Any]) -> str:
    end_at = activity["end_at"]

    if isinstance(end_at, str):
        end_at = datetime.fromisoformat(end_at)

    end_date = end_at.strftime("%d.%m.%Y %H:%M")
    type_prefix = f"[Тип {activity['type_id']}] " if activity.get("type_id") else ""
    summary = get_summary_from_url(activity["url"])

    return (
        f"<b>{type_prefix}{activity['name']}</b>\n"
        f"{activity['description']}\n\n"
        f"<blockquote>{summary}</blockquote>\n\n"
        f"<b>Окончание:</b> {end_date}\n"
        f"<b>Прямая ссылка:</b> <a href=\"{activity['url']}\">акция</a>\n\n"
        f"<a href=\"{TG_CHANNEL_URL}\">{TG_POST_DESC}</a>\n\n"
    )


def find_new_activities(
    activities: list[dict[str, Any]],
    known_ids: set[str],
) -> list[dict[str, Any]]:
    return [
        activity
        for activity in activities
        if str(activity["id"]) not in known_ids
    ]


def run_once(parser: GateParser, known_ids: set[str]) -> None:
    print(f"\n [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking activities...")

    raw_activities = parser.fetch_all_types(TYPE_IDS)
    activities = [parser.normalize(activity) for activity in raw_activities]
    new_activities = find_new_activities(activities, known_ids)

    save_activities(activities)

    if not new_activities:
        print("No new activities")
        return

    print(f"Found {len(new_activities)} new activities")

    for activity in new_activities:
        activity_id = str(activity["id"])
        message = format_activity_message(activity)
        photo_url = activity.get("image")

        if send_telegram_message(message, photo_url):
            print(f"Sent: {activity['name']}")
            known_ids.add(activity_id)
            save_known_ids(known_ids)
            time.sleep(TG_MSG_SEND_DELAY)
            continue

        print(f"Failed to send: {activity['name']} ({activity_id})")


def main() -> None:
    print("Starting Gate.com parser and Telegram bot")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing")
        return

    try:
        cookies = load_netscape_cookies(COOKIES_FILE)
    except Exception as error:
        print(f"Failed to load cookies: {error}")
        return

    parser = GateParser(cookies)
    known_ids = load_known_ids()

    print(f"Known ids: {len(known_ids)}")
    print(f"Type ids: {TYPE_IDS}")

    while True:
        try:
            run_once(parser, known_ids)
        except Exception as error:
            print(f"Loop failed: {error}")
            traceback.print_exc()

        print(f"Waiting {POLLING_INTERVAL} seconds...")
        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()