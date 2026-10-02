from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from database import (
    get_match,
    get_lang,
    get_votes,
    latest_open,
    record_vote,
    set_match_view,
    close_match,
)
from strings import t
from utils import refresh, is_admin


async def cast(bot, mid: int, user, status: str) -> bool:
    changed = record_vote(mid, user.id, user.full_name, status)
    if changed:
        await refresh(bot, mid)
    return changed


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split(":")
    m = get_match(int(parts[1]))
    lang = get_lang(q.message.chat_id)
    if not m or not m["open"]:
        await q.answer(t(lang, "closed_alert"), show_alert=True)
        return
    if parts[0] == "v":
        changed = await cast(ctx.bot, m["id"], q.from_user, parts[2])
        if parts[2] == "ATTEND":
            key = "you_yes" if changed else "already_yes"
        else:
            key = "you_no" if changed else "already_no"
        await q.answer(t(lang, key))
    else:
        new = "not" if m["view"] == "attend" else "attend"
        set_match_view(m["id"], new)
        await refresh(ctx.bot, m["id"])
        await q.answer()


async def _cmd_vote(update: Update, ctx: ContextTypes.DEFAULT_TYPE, status: str):
    chat_id = update.effective_chat.id
    m = latest_open(chat_id)
    if not m:
        await update.message.reply_text(t(get_lang(chat_id), "no_open"))
        return
    user = update.effective_user
    if status == "FLIP":
        row = next((v for v in get_votes(m["id"]) if v["user_id"] == user.id), None)
        status = "NOT" if row and row["status"] == "ATTEND" else "ATTEND"
    await cast(ctx.bot, m["id"], user, status)
    try:
        await update.message.delete()
    except TelegramError:
        pass


async def cmd_attend(u, c):
    await _cmd_vote(u, c, "ATTEND")


async def cmd_notattend(u, c):
    await _cmd_vote(u, c, "NOT")


async def cmd_change(u, c):
    await _cmd_vote(u, c, "FLIP")


async def cmd_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not await is_admin(ctx.bot, chat.id, update.effective_user.id):
        await update.message.reply_text(t(lang, "only_admin"))
        return
    m = latest_open(chat.id)
    if not m:
        await update.message.reply_text(t(lang, "no_open"))
        return
    close_match(m["id"])
    await refresh(ctx.bot, m["id"])
    try:
        await ctx.bot.unpin_chat_message(chat.id, m["message_id"])
    except TelegramError:
        pass