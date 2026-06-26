import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot token from BotFather ─────────────────────────────────────────────────
BOT_TOKEN = os.getenv("8681823299:AAG0aSwMfcszmCn8r2xrlWxmrP8BMdcCLVQ", "8681823299:AAG0aSwMfcszmCn8r2xrlWxmrP8BMdcCLVQ")

# ─── Your Telegram user ID (get it from @userinfobot) ─────────────────────────
ADMIN_IDS = [int(x) for x in os.getenv("5045900150").split(",")]

# ─── Channels users MUST join before getting files ────────────────────────────
# Format: {"name": "Display Name", "username": "@channel", "url": "invite link"}
REQUIRED_CHANNELS = [
    {
        "name": "Wavemovies",
        "username": "@wavemovies",          # ← replace with your channel username
        "url": "https://t.me/wavemovies",   # ← replace with your channel link
    },
    # Add a second channel if you want, otherwise delete this block
    # {
    #     "name": "Wavemovies Updates",
    #     "username": "@wavemovies_updates",
    #     "url": "https://t.me/wavemovies_updates",
    # },
]

# ─── MongoDB connection string ────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Rookie:Rich1234@cluster0.uoihima.mongodb.net/?appName=Cluster0")
DB_NAME = "wavemovies"

# ─── Bot display settings ────────────────────────────────────────────────────
BOT_NAME = "Wavemovies"
WELCOME_TEXT = (
    "Welcome to *Wavemovies* your premium movie file bot!\n\n"
    "📽 Use a movie link shared from our channel to get any file instantly.\n\n"
    " *Tip:* Join our channel to get new movie links daily."
)
