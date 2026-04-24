import re
import sys

import requests


JINA_READER_URL = "https://r.jina.ai/"
MAX_LINES = 80
MAX_CHARS = 5000
TIMEOUT = 30
DEBUG = False

JINA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

INLINE_LINK_RE = re.compile(r"\[([^\]]*)\]\(https?://[^\)]+\)")
INLINE_IMAGE_RE = re.compile(r"!\[.*?\]\(.*?\)")
IMAGE_ONLY_RE = re.compile(r"^!\[.*?\]\(.*?\)$")
LINK_ONLY_RE = re.compile(r"^\[\]\(https?://[^\)]+\)$")
AVATAR_SPAM_RE = re.compile(r"GateUser-\w+\s+Received|avator|!Image\s*\d+", re.IGNORECASE)
JUNK_SYMBOLS_RE = re.compile(r"^[\s\-\–\—\|*#]{2,}$")
JINA_META_RE = re.compile(r"^(Title:|URL Source:|Markdown Content:)")
SECTION_TITLE_RE = re.compile(r"^#{1,3}\s+|^[A-Z][\w\s&\-]+:\s*$")
NUMBERED_LIST_RE = re.compile(r"^\d+\.\s+")
TABLE_RE = re.compile(r"\|.*\|.*\|")

UI_NOISE_RE = re.compile(
    r"Color Preference|Change & Chart|"
    r"It seems that you're accessing our website from the US region|"
    r"Select Language|Scan the QR code|"
    r"There are currently no new notifications|"
    r"Trade Crypto Anywhere Anytime|Need Help\?|"
    r"BTC 现在值得投资吗？Shift \+ /",
    re.IGNORECASE,
)

FOOTER_SECTION_RE = re.compile(
    r"^(How to Buy Crypto|Crypto Price Prediction|Crypto to Fiat Converter|"
    r"About|Products|Services|Learn|Gate ©)",
    re.IGNORECASE,
)

LANGUAGE_LINE_RE = re.compile(
    r"^\*\s+(?:English|简体中文|Tiếng Việt|繁體中文|Español|Русский|"
    r"Français|Português|Bahasa Indonesia|日本語|العربية|Українська|"
    r"Deutsch|Türkçe)$"
)

VALUE_RE = re.compile(
    r"[\$€¥]?\s*\d+[\d,]*(\.\d+)?\s*[A-Z]{2,6}|"
    r"\d+%|"
    r"\b(?:up\s+to|max|min|at\s+least|≥|≤|more\s+than)\s*\d+",
    re.IGNORECASE,
)

ACTION_RE = re.compile(
    r"\b(deposit|trade|complete|receive|earn|win|get|claim|share|"
    r"airdrop|reward|bonus|prize|volume|check.in|register|join|task)\b",
    re.IGNORECASE,
)

TIME_RE = re.compile(
    r"\d{4}[/\-]\d{2}[/\-]\d{2}|"
    r"\d+\s*(?:days?|hours?|business\s+days)|"
    r"\b(deadline|ends?|until|valid|period)\b",
    re.IGNORECASE,
)

NAV_NOISE_RE = re.compile(
    r"Scan.*QR|Download.*App|Win.*USDT|More Download Options",
    re.IGNORECASE,
)


def fetch_clean_text(url: str) -> str:
    try:
        response = requests.get(
            f"{JINA_READER_URL}{url}",
            timeout=TIMEOUT,
            headers=JINA_HEADERS,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        print(f"❌ Fetch error: {error}", file=sys.stderr)
        return ""


def is_important_line(line: str) -> bool:
    has_value = VALUE_RE.search(line)
    has_action = ACTION_RE.search(line)
    has_time = TIME_RE.search(line)

    return any(
        (
            TABLE_RE.search(line),
            NUMBERED_LIST_RE.search(line),
            SECTION_TITLE_RE.search(line),
            has_value and has_action,
            has_time and (has_value or has_action),
        )
    )


def is_noise_line(line: str) -> bool:
    return any(
        (
            IMAGE_ONLY_RE.match(line),
            LINK_ONLY_RE.match(line),
            JINA_META_RE.match(line),
            JUNK_SYMBOLS_RE.match(line),
            UI_NOISE_RE.search(line),
            AVATAR_SPAM_RE.search(line),
            FOOTER_SECTION_RE.match(line),
            LANGUAGE_LINE_RE.match(line),
        )
    )


def clean_inline_markup(line: str) -> str:
    line = INLINE_LINK_RE.sub(r"\1", line)
    line = INLINE_IMAGE_RE.sub("", line)

    return line.strip()


def should_keep_line(line: str) -> bool:
    if is_important_line(line):
        return True

    if len(line) <= 45:
        return False

    if not re.search(r"[a-zA-Zа-яА-Я0-9]", line):
        return False

    return not NAV_NOISE_RE.search(line)


def dedupe_consecutive(lines: list[str]) -> list[str]:
    deduped = []

    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return deduped


def clean_jina_markdown(text: str) -> str:
    cleaned = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or is_noise_line(line):
            continue

        line = clean_inline_markup(line)

        if len(line) < 3:
            continue

        if should_keep_line(line):
            cleaned.append(line)

        if DEBUG:
            status = "keep" if cleaned and cleaned[-1] == line else "drop"
            print(f"[{status}] {line[:80]}")

    lines = dedupe_consecutive(cleaned)

    return "\n".join(lines[:MAX_LINES])[:MAX_CHARS]


def process_campaign(url: str) -> str:
    print(f"⏳ Processing: {url}")

    raw_text = fetch_clean_text(url)

    if not raw_text:
        return "⚠️ Failed to fetch campaign page."

    cleaned_text = clean_jina_markdown(raw_text)

    if not cleaned_text.strip():
        return "⚠️ Campaign page has no useful text."

    return cleaned_text