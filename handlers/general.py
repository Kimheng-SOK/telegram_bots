from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from database import get_lang, set_lang, latest_open
from strings import HELP_TEXT, t
from utils import is_admin, refresh


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text(
            "Use /lang inside your group. / សូមប្រើ /lang នៅក្នុងក្រុម。"
        )
        return
    if not await is_admin(ctx.bot, chat.id, update.effective_user.id):
        await update.message.reply_text(t(get_lang(chat.id), "only_admin"))
        return
    kb = Markup(
        [
            [Btn("English", callback_data="lang:en"), Btn("ខ្មែរ", callback_data="lang:km")],
            [Btn("English + ខ្មែរ", callback_data="lang:both")],
        ]
    )
    await update.message.reply_text("🌐 Language / ភាសា", reply_markup=kb)
    try:
        await update.message.delete()
    except TelegramError:
        pass


async def on_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    chat_id = q.message.chat_id
    if not await is_admin(ctx.bot, chat_id, q.from_user.id):
        await q.answer(t(get_lang(chat_id), "only_admin"), show_alert=True)
        return
    set_lang(chat_id, q.data.split(":")[1])
    await q.answer("✅")
    m = latest_open(chat_id)
    if m:
        await refresh(ctx.bot, m["id"])
    try:
        await q.message.delete()
    except TelegramError:
        pass