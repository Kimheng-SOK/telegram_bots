import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "matches.db"
DEFAULT_LANG = "both"  # "en", "km", or "both"