import asyncio

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from database import (
    engine,
    get_match,
    get_lang,
    get_votes,
    latest_open,
    record_vote,
    set_match_view,
    close_match,
    reopen_match,
    get_latest_match
)
from strings import t
from utils import refresh, is_admin, delete_after, clean



def get_val(obj, key, default=None):
    """Safely retrieves property whether obj is a dict or a SQLModel object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


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

    if not m or not get_val(m, "open"):
        await q.answer(t(lang, "closed_alert"), show_alert=True)
        return

    m_id = get_val(m, "id")
    m_view = get_val(m, "view")

    if parts[0] == "v":
        changed = await cast(ctx.bot, m_id, q.from_user, parts[2])
        if parts[2] == "ATTEND":
            key = "you_yes" if changed else "already_yes"
        else:
            key = "you_no" if changed else "already_no"
        await q.answer(t(lang, key), show_alert=True)
    else:
        new = "not" if m_view == "attend" else "attend"
        set_match_view(m_id, new)
        await refresh(ctx.bot, m_id)
        await q.answer()


async def _cmd_vote(update: Update, ctx: ContextTypes.DEFAULT_TYPE, status: str):
    chat_id = update.effective_chat.id
    m = latest_open(chat_id)
    if not m:
        await update.message.reply_text(t(get_lang(chat_id), "no_open"))
        return

    m_id = get_val(m, "id")
    user = update.effective_user

    if status == "FLIP":
        votes = get_votes(m_id)
        row = next((v for v in votes if get_val(v, "user_id") == user.id), None)
        status = "NOT" if row and get_val(row, "status") == "ATTEND" else "ATTEND"

    await cast(ctx.bot, m_id, user, status)
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
    chat_id = chat.id
    user_id = update.effective_user.id
    lang = get_lang(chat.id)

    # 1. Instantly delete the user's /close command trigger to keep chat clean
    asyncio.create_task(delete_after(ctx.bot, chat_id, update.message.message_id, 0))

    # 2. Check admin privileges (auto-delete error alert after 5s)
    if not await is_admin(ctx.bot, chat_id, user_id):
        err_msg = await ctx.bot.send_message(chat_id, t(lang, "only_admin"))
        asyncio.create_task(delete_after(ctx.bot, chat_id, err_msg.message_id, 5))
        return

    # 3. Check for active open match (auto-delete notice after 5s)
    m = latest_open(chat.id)
    if not m:
        err_msg = await ctx.bot.send_message(chat_id, t(lang, "no_open"))
        asyncio.create_task(delete_after(ctx.bot, chat_id, err_msg.message_id, 5))
        return

    m_id = get_val(m, "id")
    m_msg_id = get_val(m, "message_id")

    # 4. Close match in DB and refresh the live pinned card UI
    close_match(m_id)
    await refresh(ctx.bot, m_id)

    # 5. Unpin the match card from the group
    try:
        if m_msg_id:
            await ctx.bot.unpin_chat_message(chat.id, m_msg_id)
    except TelegramError:
        pass

    # Optional: Schedule the closed match card to auto-delete after 2 hours (7200 seconds)
    # if m_msg_id:
    #     asyncio.create_task(delete_after(ctx.bot, chat_id, m_msg_id, 7200))



async def cmd_reopen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # 1. Verify admin permissions
    if not await is_admin(context.bot, chat_id, user_id):
        msg = await update.message.reply_text("❌ Only admins can reopen the match.")
        asyncio.create_task(delete_after(context.bot, chat_id, msg.message_id, 5))
        return

    # 2. Extract match ID (either from command args e.g. /reopen 12, or default to the last closed match)
    match_id = None
    if context.args and context.args[0].isdigit():
        match_id = int(context.args[0])
    else:
        match = get_latest_match(chat_id)
        if match:
            match_id = match.id

    if not match_id:
        msg = await update.message.reply_text("❌ No match found to reopen.")
        asyncio.create_task(delete_after(context.bot, chat_id, msg.message_id, 5))
        return

    # 3. Reopen in DB and refresh the message (restores voting buttons)
    reopen_match(match_id)
    await refresh(context.bot, match_id)

    # Clean up the command message and send feedback
    await clean(context.bot, chat_id, [update.message.message_id])
    confirm = await update.message.reply_text("🔓 Match form has been reopened!")
    asyncio.create_task(delete_after(context.bot, chat_id, confirm.message_id, 5))