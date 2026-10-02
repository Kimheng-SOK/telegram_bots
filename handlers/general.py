import asyncio
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from database import get_lang, set_lang, latest_open
from strings import t
from utils import is_admin, refresh, delete_after


# async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(HELP_TEXT)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = get_lang(chat_id)

    #1. Send help message
    help_msg = await update.message.reply_text(
        t(lang, "help_text"),
        parse_mode="HTMl"
    )

    # 2. Auto-delete user's /help command and bot's reply after 2 minutes (120s)
    asyncio.create_task(delete_after(ctx.bot, chat_id, update.message.message_id, 20))
    asyncio.create_task(delete_after(ctx.bot, chat_id, help_msg.message_id, 20))



async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    lang = get_lang(chat_id)

    # Delete the command trigger instantly
    asyncio.create_task(delete_after(ctx.bot, chat_id, update.message.message_id, 0))

    # Check admin rights (fixed key from "only admin" -> "only_admin")
    if not await is_admin(ctx.bot, chat_id, user_id):
        err_msg = await ctx.bot.send_message(chat_id, t(lang, "only_admin"))
        asyncio.create_task(delete_after(ctx.bot, chat_id, err_msg.message_id, 5))
        return

    kb = Markup([
        [
            Btn("🇬🇧 English", callback_data="lang:en"),
            Btn("🇰🇭 ភាសាខ្មែរ", callback_data="lang:km"),
        ],
        [Btn("🇬🇧 / 🇰🇭 Both", callback_data="lang:both")],
    ])

    # Send using bot context directly to prevent race condition with deleted reply
    prompt = await ctx.bot.send_message(
        chat_id=chat_id,
        text=t(lang, "select_lang"),
        reply_markup=kb,
    )

    # Store prompt message ID to delete upon selection
    ctx.user_data["lang_prompt_id"] = prompt.message_id


async def on_lang_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat_id
    parts = q.data.split(":")
    selected_lang = parts[1]

    # Set new language in DB
    set_lang(chat_id, selected_lang)

    # 1. Delete the language menu prompt immediately
    asyncio.create_task(delete_after(ctx.bot, chat_id, q.message.message_id, 0))

    # 2. Optional: Send brief confirmation alter that self-destructs in 4 seconds
    confirm_msg = await ctx.bot.send_message(
        chat_id,
        t(selected_lang, "lang_updated")
    )
    asyncio.create_task(delete_after(ctx.bot, chat_id, confirm_msg.message_id, 4))