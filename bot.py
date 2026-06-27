import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.verify import verify_handler
from handlers.admin import (
    store_file_handler,
    admin_stats_handler,
    admin_batches_handler,
    admin_delete_handler,
    batch_start_handler,
    batch_done_handler,
    batch_cancel_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ── User commands ──────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))

    # ── Admin commands ─────────────────────────────────────────
    app.add_handler(CommandHandler("stats", admin_stats_handler))
    app.add_handler(CommandHandler("batches", admin_batches_handler))
    app.add_handler(CommandHandler("delete", admin_delete_handler))
    app.add_handler(CommandHandler("batch", batch_start_handler))
    app.add_handler(CommandHandler("done", batch_done_handler))
    app.add_handler(CommandHandler("cancel", batch_cancel_handler))

    # ── Inline button callbacks (force-join verify) ────────────
    app.add_handler(CallbackQueryHandler(verify_handler, pattern=r"^verify_"))

    # ── Admin file upload handler ──────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.Document.ALL | filters.VIDEO | filters.PHOTO,
            store_file_handler,
        )
    )

    logger.info("Wavemovies bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
