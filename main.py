import logging
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from config import BOT_TOKEN
from database import init_db
from handlers.general import cmd_lang, on_lang_button, cmd_help
from handlers.voting import on_button, cmd_attend, cmd_notattend, cmd_change, cmd_close, cmd_reopen, cb_reopen_confirm, cb_close_confirm
from handlers.match_wizard import newmatch, got_form, confirm, cancel, FORM, CONFIRM
from utils import schedule_command_deletion

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("match_bot")

async def auto_delete_user_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts all incoming user commands and schedules them for auto-deletion."""
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    # ⏱️ Set your delay here: 900 = 15 minutes | 3600 = 1 hour
    DELAY_SECONDS = 5

    schedule_command_deletion(context, chat_id, message_id, delay_seconds=DELAY_SECONDS)


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
    app.add_handler(CommandHandler("reopen", cmd_reopen))

    # Callback query for language selection buttons
    app.add_handler(CallbackQueryHandler(on_button, pattern=r"^(v|t):"))
    app.add_handler(CallbackQueryHandler(on_lang_button, pattern=r"^lang:"))

    app.add_handler(
        MessageHandler(filters.COMMAND, auto_delete_user_commands),
        group=1
    )

    # Callback Handler for button click
    app.add_handler(
        CallbackQueryHandler(cb_reopen_confirm, pattern=r"^act_reopen:\d+$")
    )
    app.add_handler(
        CallbackQueryHandler(cb_close_confirm, pattern=r"^act_close:\d+$")
    )

    print("⚽ Match Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()