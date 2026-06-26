import uuid
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import ADMIN_IDS
from utils.database import save_file, count_files, count_users


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def store_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin sends a file (document/video/photo) to the bot.
    Bot saves it and replies with the shareable deep link.
    """
    user = update.effective_user

    if not is_admin(user.id):
        # Silently ignore non-admins uploading files
        return

    message = update.message
    bot_username = (await context.bot.get_me()).username

    # Detect file type and extract file_id
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
        default_caption = message.document.file_name or "Movie file"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
        default_caption = message.caption or "Video file"
    elif message.photo:
        file_id = message.photo[-1].file_id  # highest resolution
        file_type = "photo"
        default_caption = message.caption or "Photo"
    else:
        return

    # Use caption from admin message if provided, else default
    caption = message.caption or f"🎬 *{default_caption}*\n\nEnjoy! — *Wavemovies*"

    # Generate a short unique key
    file_key = uuid.uuid4().hex[:10]

    await save_file(file_key, {
        "key": file_key,
        "file_id": file_id,
        "file_type": file_type,
        "caption": caption,
        "original_name": default_caption,
    })

    deep_link = f"https://t.me/{bot_username}?start={file_key}"

    await message.reply_text(
        f"✅ *File stored!*\n\n"
        f"🔑 Key: `{file_key}`\n"
        f"📁 Type: {file_type}\n\n"
        f"🔗 *Share this link:*\n`{deep_link}`\n\n"
        f"Post this link in your channel and users will get the file after joining!",
        parse_mode=ParseMode.MARKDOWN,
    )


async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics to admins."""
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("⛔ Admin only command.")
        return

    total_files = await count_files()
    total_users = await count_users()

    await update.message.reply_text(
        f"📊 *Wavemovies Stats*\n\n"
        f"👥 Total users: `{total_users}`\n"
        f"🎬 Total files: `{total_files}`",
        parse_mode=ParseMode.MARKDOWN,
    )
