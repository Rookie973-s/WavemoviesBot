import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.database import get_file, get_batch
from utils.membership import check_membership


async def verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    data = query.data  # e.g. "verify_abc123" or "verify_BATCH-abc123" or "verify_none"

    # ── DEBUG ─────────────────────────────────────────────────
    print(f"DEBUG verify_handler: data={data!r}")

    key = data.replace("verify_", "", 1) or None
    if key == "none":
        key = None

    print(f"DEBUG key resolved to: {key!r}")
    # ─────────────────────────────────────────────────────────

    not_joined = await check_membership(context.bot, user.id)

    if not_joined:
        buttons = []
        for ch in not_joined:
            buttons.append([InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["url"])])

        callback_data = f"verify_{key}" if key else "verify_none"
        buttons.append([InlineKeyboardButton("✅ I've Joined — Check Again", callback_data=callback_data)])

        await query.edit_message_text(
            "❌ You haven't joined all channels yet.\n\nPlease join and tap the button again:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # ── Verified ─────────────────────────────────────────────
    await query.edit_message_text("✅ Verified! Sending your file(s) now...")

    print(f"DEBUG user verified, delivering key={key!r}")

    if not key:
        await context.bot.send_message(
            chat_id=user.id,
            text="🎬 You're all set! Use a movie link to get a file.",
        )
        return

    # Route to batch or single file
    if key.startswith("BATCH-"):
        await _deliver_batch(context, user.id, key)
    else:
        await _deliver_file(context, user.id, key)


async def _deliver_batch(context, chat_id: int, batch_key: str):
    batch = await get_batch(batch_key)

    if not batch:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ This batch link is invalid or has expired.",
        )
        return

    files = batch.get("files", [])
    title = batch.get("title", "Batch")

    if not files:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ This batch is empty.")
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📦 *{title}*\n\nSending {len(files)} file{'s' if len(files) != 1 else ''} now...",
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

        if i < len(files):
            await asyncio.sleep(0.5)


async def _deliver_file(context, chat_id: int, file_key: str):
    print(f"DEBUG _deliver_file: looking up file_key={file_key!r}")
    record = await get_file(file_key)
    print(f"DEBUG _deliver_file: record found = {record is not None}")

    if not record:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ This link is invalid or the file has been removed.",
        )
        return

    file_id = record["file_id"]
    file_type = record.get("file_type", "document")
    caption = record.get("caption", "🎬 Enjoy your movie! — *Wavemovies*")

    await _send_file(context.bot, chat_id, file_id, file_type, caption)


async def _send_file(bot, chat_id: int, file_id: str, file_type: str, caption: str):
    kwargs = dict(chat_id=chat_id, caption=caption, parse_mode=ParseMode.MARKDOWN)

    if file_type == "document":
        await bot.send_document(document=file_id, **kwargs)
    elif file_type == "video":
        await bot.send_video(video=file_id, **kwargs)
    elif file_type == "photo":
        await bot.send_photo(photo=file_id, **kwargs)
