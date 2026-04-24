import os
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(ENV_PATH)


API_KEY = os.getenv("CLOUD_API")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("MODEL", "Qwen/Qwen3-Coder-Next")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.5"))
TOP_P = float(os.getenv("TOP_P", "0.45"))