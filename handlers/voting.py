import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    get_latest_match,
    get_match_by_id
)
from strings import t
from utils import refresh, is_admin, delete_after, clean, pin_match_card



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


# 1. Slash Command: sends the confirm button panel
async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    lang = get_lang(chat_id)

    # Clean up command message immediately
    await clean(context.bot, chat_id, [update.message.message_id])

    # Check admin permissions
    if not await is_admin(context.bot, chat_id, user_id):
        msg = await context.bot.send_message(
            chat_id=chat_id, text=t(lang, "only_admin")
        )
        asyncio.create_task(delete_after(context.bot, chat_id, msg.message_id, 5))
        return

    # Extract target match
    match_id = None
    if context.args and context.args[0].isdigit():
        match_id = int(context.args[0])
    else:
        match = get_latest_match(chat_id)
        if match:
            match_id = match.id

    if not match_id:
        msg = await context.bot.send_message(
            chat_id=chat_id, text=t(lang, "no_match_found")
        )
        asyncio.create_task(delete_after(context.bot, chat_id, msg.message_id, 5))
        return

    # Send action button panel
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t(lang, "btn_confirm_close"),
                    callback_data=f"act_close:{match_id}",
                )
            ]
        ]
    )

    panel = await context.bot.send_message(
        chat_id=chat_id, text=t(lang, "close_prompt"), reply_markup=kb
    )
    asyncio.create_task(delete_after(context.bot, chat_id, panel.message_id, 30))


# 2. Callback Query: closes match, unpins card, & triggers pop-up alert
async def cb_close_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    chat_id = q.message.chat_id
    user_id = q.from_user.id
    lang = get_lang(chat_id)

    # Verify admin on click
    if not await is_admin(context.bot, chat_id, user_id):
        await q.answer(t(lang, "only_admin"), show_alert=True)
        return

    match_id = int(q.data.split(":")[1])

    # Close match in DB and refresh UI card (disables voting buttons)
    close_match(match_id)
    await refresh(context.bot, match_id)

    # Unpin match card message
    target_match = get_match_by_id(match_id)
    if target_match and target_match.message_id:
        try:
            await context.bot.unpin_chat_message(
                chat_id=chat_id, message_id=target_match.message_id
            )
        except Exception:
            pass  # Ignores error if message was already unpinned or deleted

        # Schedule match card deletion in 4 hours (14400 seconds)
        context.job_queue.run_once(
            delete_job_callback,
            when=14400,
            data={"chat_id": chat_id, "message_id": target_match.message_id},
            name=f"auto_del_match_{chat_id}_{target_match.message_id}",
        )

    # Delete prompt panel
    await clean(context.bot, chat_id, [q.message.message_id])

    # Pop-Up Alert Modal
    await q.answer(t(lamg, "alert_match_closed"), show_alert=True)


async def cmd_reopen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    lang = get_lang(chat_id)

    # 1. Clean up the /reopen command message
    await clean(context.bot, chat_id, [update.message.message_id])

    # 2. Check admin permissions
    if not await is_admin(context.bot, chat_id, user_id):
        msg = await context.bot.send_message(
            chat_id=chat_id, text=t(lang, "only_admin")
        )
        asyncio.create_task(delete_after(context.bot, chat_id, msg.message_id, 5))
        return

    # 3. Get target match ID
    match_id = None
    if context.args and context.args[0].isdigit():
        match_id = int(context.args[0])
    else:
        match = get_latest_match(chat_id)
        if match:
            match_id = match.id

    if not match_id:
        msg = await context.bot.send_message(
            chat_id=chat_id, text=t(lang, "no_match_found")
        )
        asyncio.create_task(delete_after(context.bot, chat_id, msg.message_id, 5))
        return

    # 4. Send action button panel for the admin to confirm reopening
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t(lang, "btn_confirm_reopen"),
                    callback_data=f"act_reopen:{match_id}",
                )
            ]
        ]
    )

    panel = await context.bot.send_message(
        chat_id=chat_id, text=t(lang, "reopen_prompt"), reply_markup=kb
    )
    asyncio.create_task(delete_after(context.bot, chat_id, panel.message_id, 30))


async def cb_reopen_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    chat_id = q.message.chat_id
    user_id = q.from_user.id
    lang = get_lang(chat_id)

    # 1. Verify admin permissions
    if not await is_admin(context.bot, chat_id, user_id):
        await q.answer(t(lang, "only_admin"), show_alert=True)
        return

    match_id = int(q.data.split(":")[1])

    # 2. Reopen match in DB & refresh UI card
    reopen_match(match_id)
    await refresh(context.bot, match_id)

    # 3. Re-pin the match card message
    target_match = get_match_by_id(match_id)
    if target_match and target_match.message_id:
        await pin_match_card(context.bot, chat_id, target_match.message_id)

        # Cancel pending auto-delete job if match is reopened
        job_name = f"auto_del_match_{chat_id}_{target_match.message_id}"
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()

    # 4. Clean up prompt panel message
    await clean(context.bot, chat_id, [q.message.message_id])
    # 5. Native Telegram Pop-Up Alert
    await q.answer(t(lang, "alert_match_reopened"), show_alert=True)