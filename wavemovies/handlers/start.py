from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import WELCOME_TEXT
from utils.database import get_file, save_user
from utils.membership import check_membership


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_user(user.id, user.username, user.full_name)

    args = context.args  # file key passed via t.me/bot?start=KEY
    file_key = args[0] if args else None


    not_joined = await check_membership(context.bot, user.id)

    if not_joined:
        await _send_join_prompt(update, not_joined, file_key)
        return


    if file_key:
        await _deliver_file(update, context, file_key)
    else:
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode=ParseMode.MARKDOWN,
        )


async def _send_join_prompt(update: Update, channels: list, file_key: str | None):
    """Send the force-join message with channel buttons."""
    lines = ["🔒 *Access Required*\n", "To get this file, join our channel(s) first:\n"]

    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["url"])])

    callback_data = f"verify_{file_key}" if file_key else "verify_none"
    buttons.append([InlineKeyboardButton("✅ I've Joined — Check Again", callback_data=callback_data)])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _deliver_file(update: Update, context: ContextTypes.DEFAULT_TYPE, file_key: str):
    """Look up the file key and send the file to the user."""
    record = await get_file(file_key)

    if not record:
        await update.message.reply_text(
            "⚠️ This link is invalid or the file has been removed."
        )
        return

    chat_id = update.effective_chat.id
    caption = record.get("caption", "🎬 Enjoy your movie! — *Wavemovies*")
    file_id = record["file_id"]
    file_type = record.get("file_type", "document")

    send_map = {
        "document": context.bot.send_document,
        "video": context.bot.send_video,
        "photo": context.bot.send_photo,
    }

    sender = send_map.get(file_type, context.bot.send_document)
    kwargs = {
        "chat_id": chat_id,
        file_type if file_type != "document" else "document": file_id,
        "caption": caption,
        "parse_mode": ParseMode.MARKDOWN,
    }

    # python-telegram-bot uses keyword arg matching the media type
    if file_type == "document":
        await context.bot.send_document(chat_id=chat_id, document=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
    elif file_type == "video":
        await context.bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
    elif file_type == "photo":
        await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
