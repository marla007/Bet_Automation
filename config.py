"""Project settings, read from environment variables or a local .env file."""

import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app").rstrip("/")
USER_ID = os.getenv("USER_ID", "")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
