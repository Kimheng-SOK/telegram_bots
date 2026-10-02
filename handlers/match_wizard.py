from telegram import Update, ForceReply, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler

from database import get_lang, create_match, update_match_message_id, get_match
from strings import TEMPLATES, STR, FIELD_LABELS, t, pick
from utils import parse_form, render, keyboard, clean

FORM, CONFIRM = range(2)


def _force_reply():
    return ForceReply(selective=True, input_field_placeholder="Paste the filled form here")


async def newmatch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "Please run /newmatch inside your team group. / សូមប្រើ /newmatch នៅក្នុងក្រុម。"
        )
        return ConversationHandler.END
    lang = get_lang(update.effective_chat.id)
    keys = {"en": ["en"], "km": ["km"], "both": ["en", "km"]}[lang]
    forms = "\n".join(f"<pre>{TEMPLATES[k]}</pre>" for k in keys)
    prompt = await update.message.reply_text(
        f"📝 <b>{t(lang, 'form_title')}</b>\n{t(lang, 'form_help')}\n\n{forms}\n/cancel",
        parse_mode=ParseMode.HTML,
        reply_markup=_force_reply(),
    )
    ctx.user_data["cleanup"] = [update.message.message_id, prompt.message_id]
    return FORM


async def got_form(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.setdefault("cleanup", []).append(update.message.message_id)
    lang = get_lang(update.effective_chat.id)
    data, missing = parse_form(update.message.text)
    if missing:
        names = ", ".join(pick(lang, FIELD_LABELS[k]) for k in missing)
        msg = await update.message.reply_text(
            f"⚠️ {t(lang, 'missing')} {names}\n{t(lang, 'resend')}",
            reply_markup=_force_reply(),
        )
        ctx.user_data["cleanup"].append(msg.message_id)
        return FORM
    ctx.user_data["m"] = data
    preview_data = {**data, "view": "attend", "open": 1}
    kb = Markup(
        [
            [Btn(pick(lang, STR["btn_confirm"]), callback_data="ok")],
            [Btn(pick(lang, STR["btn_cancel"]), callback_data="cancel")],
        ]
    )
    preview = await update.message.reply_text(
        f"{t(lang, 'preview')}\n\n" + render(preview_data, [], lang),
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
        )
    ctx.user_data["cleanup"].append(preview.message_id)
    return CONFIRM


async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = ctx.user_data.pop("m")
    chat_id = q.message.chat_id

    mid = create_match(chat_id, d)
    m = get_match(mid)
    msg = await ctx.bot.send_message(
        chat_id,
        render(m, [], get_lang(chat_id)),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard(m),
    )
    update_match_message_id(mid, msg.message_id)

    try:
        await ctx.bot.pin_chat_message(chat_id, msg.message_id)
    except TelegramError:
        await ctx.bot.send_message(
            chat_id, "⚠️ I couldn't pin it. Give me the 'Pin messages' admin right."
        )

    await clean(ctx.bot, chat_id, ctx.user_data.pop("cleanup", []))
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ids = ctx.user_data.pop("cleanup", [])
    ctx.user_data.pop("m", None)
    chat_id = update.effective_chat.id
    if update.callback_query:
        await update.callback_query.answer("✖")
    else:
        ids.append(update.message.message_id)
    await clean(ctx.bot, chat_id, ids)
    return ConversationHandler.END