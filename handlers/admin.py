import uuid
from datetime import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import ADMIN_IDS, AUTO_DELETE_SECONDS
from utils.database import (
    save_file,
    save_batch,
    delete_file,
    delete_batch,
    get_batch,
    list_batches,
    count_files,
    count_users,
    count_batches,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _ttl_note() -> str:
    if AUTO_DELETE_SECONDS and AUTO_DELETE_SECONDS > 0:
        hours = AUTO_DELETE_SECONDS / 3600
        if hours >= 1:
            return f"⏱️ Auto-deletes in {hours:g}h"
        mins = AUTO_DELETE_SECONDS / 60
        return f"⏱️ Auto-deletes in {mins:g}m"
    return "♾️ No auto-delete"


def _format_dt(dt) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


# ─── Batch session state (in-memory per admin) ────────────────────────────────
# Structure: { admin_id: { "title": str, "files": [ {file_key, file_type, original_name} ] } }
_batch_sessions: dict[int, dict] = {}


# ─── /batch command ───────────────────────────────────────────────────────────

async def batch_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /batch [optional title]
    Starts a batch recording session. Every file sent after this is added
    to the batch until /done is called.
    """
    user = update.effective_user
    if not is_admin(user.id):
        return

    title = " ".join(context.args) if context.args else "Untitled Batch"

    # Cancel any existing session
    _batch_sessions[user.id] = {"title": title, "files": []}

    await update.message.reply_text(
        f"📦 *Batch session started!*\n\n"
        f"📝 Title: *{title}*\n\n"
        f"Now send me the files one by one. When you're done, type /done to generate the batch link.\n\n"
        f"Type /cancel to abort.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def batch_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /done
    Finalizes the current batch session and generates a shareable link.
    """
    user = update.effective_user
    if not is_admin(user.id):
        return

    session = _batch_sessions.get(user.id)
    if not session:
        await update.message.reply_text("⚠️ No active batch session. Use /batch to start one.")
        return

    files = session["files"]
    if not files:
        await update.message.reply_text("⚠️ No files were added to the batch. Send some files first.")
        return

    batch_key = "BATCH-" + uuid.uuid4().hex[:10]
    title = session["title"]

    await save_batch(batch_key, {
        "key": batch_key,
        "title": title,
        "files": files,
    })

    # Clean up session
    del _batch_sessions[user.id]

    bot_username = (await context.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start={batch_key}"

    file_list = "\n".join(
        f"  {i+1}. {f['original_name']} ({f['file_type']})"
        for i, f in enumerate(files)
    )

    await update.message.reply_text(
        f"✅ *Batch created!*\n\n"
        f"📦 Title: *{title}*\n"
        f"🗂️ Files ({len(files)}):\n{file_list}\n\n"
        f"🔑 Key: `{batch_key}`\n"
        f"{_ttl_note()}\n\n"
        f"🔗 *Share this link:*\n`{deep_link}`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def batch_cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel — abort the current batch session without saving."""
    user = update.effective_user
    if not is_admin(user.id):
        return

    if user.id in _batch_sessions:
        del _batch_sessions[user.id]
        await update.message.reply_text("🚫 Batch session cancelled.")
    else:
        await update.message.reply_text("No active batch session to cancel.")


# ─── File upload handler ───────────────────────────────────────────────────────

async def store_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin sends a file (document/video/photo).
    - If inside a batch session → add to batch.
    - Otherwise → save as individual file and reply with a link.
    """
    user = update.effective_user
    if not is_admin(user.id):
        return

    message = update.message

    if message.document:
        file_id = message.document.file_id
        file_type = "document"
        default_caption = message.document.file_name or "Movie file"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
        default_caption = message.caption or "Video file"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        default_caption = message.caption or "Photo"
    else:
        return

    caption = message.caption or f"🎬 *{default_caption}*\n\nEnjoy! — *Wavemovies*"
    file_key = uuid.uuid4().hex[:10]

    await save_file(file_key, {
        "key": file_key,
        "file_id": file_id,
        "file_type": file_type,
        "caption": caption,
        "original_name": default_caption,
    })

    # ── Batch mode ────────────────────────────────────────────
    if user.id in _batch_sessions:
        _batch_sessions[user.id]["files"].append({
            "file_key": file_key,
            "file_type": file_type,
            "original_name": default_caption,
        })
        count = len(_batch_sessions[user.id]["files"])
        await message.reply_text(
            f"✅ Added to batch ({count} file{'s' if count != 1 else ''} so far).\n"
            f"📄 `{default_caption}`\n\n"
            f"Send more files or type /done to finish.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # ── Single-file mode ──────────────────────────────────────
    bot_username = (await context.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start={file_key}"

    await message.reply_text(
        f"✅ *File stored!*\n\n"
        f"🔑 Key: `{file_key}`\n"
        f"📁 Type: {file_type}\n"
        f"{_ttl_note()}\n\n"
        f"🔗 *Share this link:*\n`{deep_link}`\n\n"
        f"_Tip: Use /batch to group multiple files into one link._",
        parse_mode=ParseMode.MARKDOWN,
    )


# ─── /batches ─────────────────────────────────────────────────────────────────

async def admin_batches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List the 20 most recent batches with their keys and file counts."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Admin only command.")
        return

    batches = await list_batches(limit=20)
    if not batches:
        await update.message.reply_text("📭 No batches found.")
        return

    bot_username = (await context.bot.get_me()).username
    lines = ["📦 *Recent Batches* (latest 20)\n"]

    for b in batches:
        key = b["key"]
        title = b.get("title", "Untitled")
        file_count = len(b.get("files", []))
        created = _format_dt(b.get("created_at"))
        expires = b.get("expires_at")
        exp_str = f"⏱️ Expires {_format_dt(expires)}" if expires else "♾️ No expiry"
        link = f"https://t.me/{bot_username}?start={key}"

        lines.append(
            f"*{title}* — {file_count} file{'s' if file_count != 1 else ''}\n"
            f"  🔑 `{key}`\n"
            f"  📅 {created} | {exp_str}\n"
            f"  🔗 [Link]({link})\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ─── /delete ──────────────────────────────────────────────────────────────────

async def admin_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /delete <key>
    Deletes a file or batch by its key.
    Batches: key starts with BATCH-
    Files: any other key
    """
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Admin only command.")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/delete <key>`\n\n"
            "Example:\n"
            "`/delete abc1234567`\n"
            "`/delete BATCH-abc1234567`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    key = context.args[0].strip()
    is_batch = key.startswith("BATCH-")

    if is_batch:
        deleted = await delete_batch(key)
    else:
        deleted = await delete_file(key)

    kind = "Batch" if is_batch else "File"

    if deleted:
        await update.message.reply_text(
            f"🗑️ *{kind} deleted successfully.*\n`{key}`",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            f"⚠️ No {kind.lower()} found with key `{key}`.\nIt may have already been deleted or expired.",
            parse_mode=ParseMode.MARKDOWN,
        )


# ─── /stats ───────────────────────────────────────────────────────────────────

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics to admins."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Admin only command.")
        return

    total_files = await count_files()
    total_users = await count_users()
    total_batches = await count_batches()
    ttl_note = _ttl_note()

    # Show active batch session info if any
    active_session = _batch_sessions.get(user.id)
    session_line = (
        f"🔄 Active batch session: *{active_session['title']}* ({len(active_session['files'])} files staged)\n"
        if active_session else ""
    )

    await update.message.reply_text(
        f"📊 *Wavemovies Stats*\n\n"
        f"👥 Total users: `{total_users}`\n"
        f"🎬 Total files: `{total_files}`\n"
        f"📦 Total batches: `{total_batches}`\n"
        f"⏱️ Auto-delete: `{ttl_note}`\n\n"
        f"{session_line}"
        f"*Admin Commands:*\n"
        f"`/batch [title]` — Start a batch\n"
        f"`/done` — Finish & generate batch link\n"
        f"`/cancel` — Abort batch session\n"
        f"`/batches` — List recent batches\n"
        f"`/delete <key>` — Delete a file or batch\n"
        f"`/stats` — This panel",
        parse_mode=ParseMode.MARKDOWN,
    )
