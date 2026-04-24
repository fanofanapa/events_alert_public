import time
from datetime import datetime
from typing import Any

import requests

from config import (
    API_BASE_URL,
    API_PARAMS_BASE,
    HEADERS,
    REQUEST_DELAY,
    TYPE_DELAY,
)


def load_netscape_cookies(filepath: str) -> str:
    cookies = []

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")

            if len(parts) >= 7:
                cookies.append(f"{parts[5]}={parts[6]}")

    if not cookies:
        print("Cookie file is empty or has no valid records")

    return "; ".join(cookies)


class GateParser:
    def __init__(self, cookies: str) -> None:
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.headers["Cookie"] = cookies

    def fetch_page(self, type_id: int, page: int) -> dict[str, Any]:
        params = {
            **API_PARAMS_BASE,
            "type_id": type_id,
            "page": page,
        }

        response = self.session.get(API_BASE_URL, params=params)
        response.raise_for_status()

        return response.json()

    def fetch_type_all(self, type_id: int) -> list[dict[str, Any]]:
        items = []
        page = 1

        while True:
            print(f"type_id={type_id}, page={page}")
            data = self.fetch_page(type_id, page)

            if data.get("code") != 0:
                print(f"API error: {data.get('message')}")
                break

            page_data = data.get("data", {})
            page_items = page_data.get("list", [])
            page_count = page_data.get("pageCount", page)

            items.extend(page_items)

            if page >= page_count:
                break

            page += 1
            time.sleep(REQUEST_DELAY)

        return items

    def fetch_all_types(self, type_ids: list[int]) -> list[dict[str, Any]]:
        activities = []

        for type_id in type_ids:
            print(f"Processing type_id={type_id}")
            items = self.fetch_type_all(type_id)

            for item in items:
                item["_type_id"] = type_id

            activities.extend(items)
            time.sleep(TYPE_DELAY)

        print(f"Loaded {len(activities)} activities")

        return activities

    @staticmethod
    def normalize(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "type_id": item.get("_type_id"),
            "name": item["competition_name"].strip(),
            "description": item.get("slave_one_line", "").strip(),
            "url": f"https://www.gate.com{item['url'].strip()}",
            "image": item.get("new_img") or item.get("img"),
            "start_at": datetime.fromtimestamp(item["start_at"]),
            "end_at": datetime.fromtimestamp(item["end_at"]),
            "hot": item.get("hot", 0),
            "fetched_at": datetime.now(),
        }