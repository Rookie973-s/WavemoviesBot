import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import WELCOME_TEXT
from utils.database import get_file, get_batch, save_user
from utils.membership import check_membership


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_user(user.id, user.username, user.full_name)

    args = context.args
    key = args[0] if args else None

    not_joined = await check_membership(context.bot, user.id)

    if not_joined:
        await _send_join_prompt(update, not_joined, key)
        return

    if key:
        await _deliver_content(update, context, key)
    else:
        await update.message.reply_text(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN)


async def _send_join_prompt(update: Update, channels: list, key: str | None):
    """Send the force-join message with channel buttons."""
    lines = ["🔒 *Access Required*\n", "To get this file, join our channel(s) first:\n"]

    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["url"])])

    callback_data = f"verify_{key}" if key else "verify_none"
    buttons.append([InlineKeyboardButton("✅ I've Joined — Check Again", callback_data=callback_data)])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _deliver_content(update, context, key: str):
    """Route to batch delivery or single-file delivery."""
    if key.startswith("BATCH-"):
        await _deliver_batch(update, context, key)
    else:
        await _deliver_file(update, context, key)


async def _deliver_batch(update, context, batch_key: str):
    """Send all files in a batch sequentially."""
    batch = await get_batch(batch_key)

    if not batch:
        await update.message.reply_text(
            "⚠️ This batch link is invalid or has expired."
        )
        return

    chat_id = update.effective_chat.id
    files = batch.get("files", [])
    title = batch.get("title", "Batch")

    if not files:
        await update.message.reply_text("⚠️ This batch is empty.")
        return

    await update.message.reply_text(
        f"📦 *{title}*\n\nSending {len(files)} file{'s' if len(files) != 1 else ''} now...",
        parse_mode=ParseMode.MARKDOWN,
    )

    for i, file_entry in enumerate(files, 1):
        file_key = file_entry["file_key"]
        record = await get_file(file_key)

        if not record:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ File {i}/{len(files)} is unavailable or expired.",
            )
            continue

        file_id = record["file_id"]
        file_type = record.get("file_type", "document")
        caption = record.get("caption", f"🎬 File {i}/{len(files)} — *Wavemovies*")

        await _send_file(context.bot, chat_id, file_id, file_type, caption)

        # Small delay between files to avoid Telegram flood limits
        if i < len(files):
            await asyncio.sleep(0.5)


async def _deliver_file(update, context, file_key: str):
    """Look up the file key and send the file to the user."""
    record = await get_file(file_key)

    if not record:
        await update.message.reply_text(
            "⚠️ This link is invalid or the file has been removed."
        )
        return

    chat_id = update.effective_chat.id
    file_id = record["file_id"]
    file_type = record.get("file_type", "document")
    caption = record.get("caption", "🎬 Enjoy your movie! — *Wavemovies*")

    await _send_file(context.bot, chat_id, file_id, file_type, caption)


async def _send_file(bot, chat_id: int, file_id: str, file_type: str, caption: str):
    """Send a single file of the given type."""
    kwargs = dict(chat_id=chat_id, caption=caption, parse_mode=ParseMode.MARKDOWN)

    if file_type == "document":
        await bot.send_document(document=file_id, **kwargs)
    elif file_type == "video":
        await bot.send_video(video=file_id, **kwargs)
    elif file_type == "photo":
        await bot.send_photo(photo=file_id, **kwargs)
