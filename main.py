import logging
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from database import init_db
from handlers.general import cmd_lang, on_lang_button, cmd_help
from handlers.voting import on_button, cmd_attend, cmd_notattend, cmd_change, cmd_close
from handlers.match_wizard import newmatch, got_form, confirm, cancel, FORM, CONFIRM

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("match_bot")


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    txt = filters.TEXT & ~filters.COMMAND

    wizard = ConversationHandler(
        entry_points=[CommandHandler("newmatch", newmatch)],
        states={
            FORM: [MessageHandler(txt, got_form)],
            CONFIRM: [
                CallbackQueryHandler(confirm, pattern=r"^ok$"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600,
    )
    app.add_handler(wizard)

    # General / Utility Handlers
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("lang", cmd_lang))

    # Voting & Match Handlers
    app.add_handler(CommandHandler("attend", cmd_attend))
    app.add_handler(CommandHandler("notattend", cmd_notattend))
    app.add_handler(CommandHandler("change", cmd_change))
    app.add_handler(CommandHandler("close", cmd_close))

    # Callback query for language selection buttons
    app.add_handler(CallbackQueryHandler(on_button, pattern=r"^(v|t):"))
    app.add_handler(CallbackQueryHandler(on_lang_button, pattern=r"^lang:"))

    print("⚽ Match Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()