import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Fallback to local SQLite file if DATABASE_URL is not set in .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

DEFAULT_LANG = os.getenv("DEFAULT_LANG", "both")