import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────
# BOT TOKEN
# ──────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set. Add BOT_TOKEN to your .env file or Railway Variables."
    )

# ──────────────────────────────────────────────────────────────
# ADMIN IDS
# ──────────────────────────────────────────────────────────────
admin_ids = os.getenv("ADMIN_IDS")

if not admin_ids:
    raise RuntimeError(
        "ADMIN_IDS is not set. Add ADMIN_IDS to your .env file or Railway Variables."
    )

try:
    ADMIN_IDS = [int(x.strip()) for x in admin_ids.split(",")]
except ValueError:
    raise RuntimeError("ADMIN_IDS must contain only numbers separated by commas.")

# ──────────────────────────────────────────────────────────────
# REQUIRED CHANNELS
# ──────────────────────────────────────────────────────────────
REQUIRED_CHANNELS = [
    {
        "name": "Wavemovies",
        "username": "@wavemovies_chn",
        "url": "https://t.me/wavemovies_chn",
    },
    {
        "name": "Wave Backup",
        "username": "-1003879166875",
        "url": "https://t.me/+hGSpcI4wK34xZjA0",
    },
    {
        "name": "Files Channel",
        "username": "-1002247736269",
        "url": "https://t.me/+ARlpOEKqMBk4MTI0",
    },
]

# ──────────────────────────────────────────────────────────────
# MONGODB
# ──────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not set. Add MONGO_URI to your .env file or Railway Variables."
    )

DB_NAME = "wavemovies"

# ──────────────────────────────────────────────────────────────
# AUTO-DELETE
# Set AUTO_DELETE_SECONDS in env to enable timed file/batch deletion.
# Examples:
#   AUTO_DELETE_SECONDS=300   →  5 minutes
#   AUTO_DELETE_SECONDS=3600  →  1 hour
#   AUTO_DELETE_SECONDS=0     →  disabled (default)
# ──────────────────────────────────────────────────────────────
_raw_ttl = os.getenv("AUTO_DELETE_SECONDS", "0")
try:
    AUTO_DELETE_SECONDS = int(_raw_ttl)
except ValueError:
    AUTO_DELETE_SECONDS = 0  # disabled if misconfigured

# ──────────────────────────────────────────────────────────────
# BOT SETTINGS
# ──────────────────────────────────────────────────────────────
BOT_NAME = "Wavemovies"

WELCOME_TEXT = (
    "🎬 Welcome to *Wavemovies*!\n\n"
    "Use a movie link shared from our channel to receive the file instantly.\n\n"
    "📢 Join our channel to get the latest movie updates."
)

# ──────────────────────────────────────────────────────────────
# WEBHOOK SETTINGS (Render Web Service)
# Render sets PORT and RENDER_EXTERNAL_URL automatically.
# Set WEBHOOK_URL yourself only if you use a custom domain.
# If neither URL is available (e.g. running locally), the bot
# falls back to polling.
# ──────────────────────────────────────────────────────────────
PORT = int(os.getenv("PORT", "10000"))

WEBHOOK_BASE_URL = (
    os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
).rstrip("/")

# URL path Telegram posts to. Not the bot token, to keep it out of logs.
WEBHOOK_PATH = "telegram-webhook"

# Telegram sends this in a header; requests without it are rejected.
# Allowed chars: A-Z a-z 0-9 _ -  (derived from the token if not set)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or hashlib.sha256(
    BOT_TOKEN.encode()
).hexdigest()
