import os
from dotenv import load_dotenv

# Load environment variables from .env (works locally)
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
# Supports one or more IDs separated by commas:
# ADMIN_IDS=5045900150
# or
# ADMIN_IDS=5045900150,123456789
# ──────────────────────────────────────────────────────────────
admin_ids = os.getenv("ADMIN_IDS")

if not admin_ids:
    raise RuntimeError(
        "ADMIN_IDS is not set. Add ADMIN_IDS to your .env file or Railway Variables."
    )

try:
    ADMIN_IDS = [int(x.strip()) for x in admin_ids.split(",")]
except ValueError:
    raise RuntimeError(
        "ADMIN_IDS must contain only numbers separated by commas."
    )

# ──────────────────────────────────────────────────────────────
# REQUIRED CHANNELS
# ──────────────────────────────────────────────────────────────
REQUIRED_CHANNELS = [
    {
        "name": "Wavemovies",
        "username": "@wavemovies",
        "url": "https://t.me/wavemovies",
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
# BOT SETTINGS
# ──────────────────────────────────────────────────────────────
BOT_NAME = "Wavemovies"

WELCOME_TEXT = (
    "🎬 Welcome to *Wavemovies*!\n\n"
    "Use a movie link shared from our channel to receive the file instantly.\n\n"
    "📢 Join our channel to get the latest movie updates."
)
