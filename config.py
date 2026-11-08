"""Static configuration, loaded from environment variables / a .env file."""
import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default=None):
    value = os.getenv(name, "").strip()
    return int(value) if value.isdigit() else default


TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
OWNER_IDS = {
    int(x) for x in os.getenv("OWNER_IDS", "").replace(" ", "").split(",") if x.isdigit()
}
DB_PATH = os.getenv("DB_PATH", "sentinel.db")
BOT_NAME = os.getenv("BOT_NAME", "Sentinel")

SYNC_COMMANDS = os.getenv("SYNC_COMMANDS", "true").strip().lower() in ("1", "true", "yes", "on")
DEV_GUILD_ID = _int("DEV_GUILD_ID")

PREMIUM_URL = os.getenv("PREMIUM_URL", "https://example.com/premium").strip()
PREMIUM_SKU_ID = _int("PREMIUM_SKU_ID")
PREMIUM_SKU_TIER = os.getenv("PREMIUM_SKU_TIER", "premium").strip().lower()
