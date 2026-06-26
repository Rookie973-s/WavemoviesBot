from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.database import get_file
from utils.membership import check_membership


async def verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    data = query.data  # e.g. "verify_abc123" or "verify_none"
    file_key = data.replace("verify_", "") or None
    if file_key == "none":
        file_key = None

    not_joined = await check_membership(context.bot, user.id)

    if not_joined:
        # Still hasn't joined — show updated prompt
        buttons = []
        for ch in not_joined:
            buttons.append([InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["url"])])

        callback_data = f"verify_{file_key}" if file_key else "verify_none"
        buttons.append([InlineKeyboardButton("✅ I've Joined — Check Again", callback_data=callback_data)])

        await query.edit_message_text(
            "❌ You haven't joined all channels yet.\n\nPlease join and tap the button again:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # ── Verified! Deliver the file ───────────────────────────────────────────
    await query.edit_message_text("✅ Verified! Sending your file now...")

    if not file_key:
        await context.bot.send_message(
            chat_id=user.id,
            text="🎬 You're all set! Use a movie link to get a file.",
        )
        return

    record = await get_file(file_key)

    if not record:
        await context.bot.send_message(
            chat_id=user.id,
            text="⚠️ This link is invalid or the file has been removed.",
        )
        return

    caption = record.get("caption", "🎬 Enjoy your movie! — *Wavemovies*")
    file_id = record["file_id"]
    file_type = record.get("file_type", "document")

    if file_type == "document":
        await context.bot.send_document(chat_id=user.id, document=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
    elif file_type == "video":
        await context.bot.send_video(chat_id=user.id, video=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
    elif file_type == "photo":
        await context.bot.send_photo(chat_id=user.id, photo=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
