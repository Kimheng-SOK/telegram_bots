"""
Telegram match-attendance bot (python-telegram-bot v21+, SQLite, long polling).

Setup:
    pip install "python-telegram-bot>=21" python-dotenv
    echo 'BOT_TOKEN=123456:ABC...' > .env
    python match_bot.py

BotFather: /setprivacy -> Disable (so the bot can read the wizard answers in groups).
Group: add the bot as admin with "Pin messages" and "Delete messages" rights.
"""
import html
import logging
import os
import sqlite3

from dotenv import load_dotenv
from telegram import InlineKeyboardButton as Btn
from telegram import InlineKeyboardMarkup as Markup
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()  # reads BOT_TOKEN from the .env file next to this script
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("match_bot")

DB = "matches.db"
DATE, START, END, SIZE, CUSTOM, LOCATION, OPPONENT, KITS, CONFIRM = range(9)
e = html.escape


# ---------------------------------------------------------------- database
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with db() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS matches(
                                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                  chat_id INTEGER, message_id INTEGER,
                                                  date TEXT, start TEXT, end TEXT, size INTEGER,
                                                  location TEXT, opponent TEXT, kits TEXT,
                                                  view TEXT DEFAULT 'attend', open INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS votes(
                                                match_id INTEGER, user_id INTEGER, name TEXT, status TEXT,
                                                updated TEXT, PRIMARY KEY(match_id, user_id));
            """
        )


def get_match(mid):
    with db() as c:
        return c.execute("SELECT * FROM matches WHERE id=?", (mid,)).fetchone()


def latest_open(chat_id):
    with db() as c:
        return c.execute(
            "SELECT * FROM matches WHERE chat_id=? AND open=1 AND message_id IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (chat_id,),
        ).fetchone()


def get_votes(mid):
    with db() as c:
        return c.execute(
            "SELECT * FROM votes WHERE match_id=? ORDER BY updated, rowid", (mid,)
        ).fetchall()


# --------------------------------------------------------------- rendering
LINE = "━━━━━━━━━━━━━━━━━━"


def render(m, votes):
    yes = [v["name"] for v in votes if v["status"] == "ATTEND"]
    no = [v["name"] for v in votes if v["status"] == "NOT"]
    size = m["size"]
    lines = [
        "⚽ <b>MATCH DAY</b> ⚽",
        LINE,
        f"📅 <b>{e(m['date'])}</b>",
        f"⏰ {e(m['start'])} – {e(m['end'])}",
        f"📍 {e(m['location'])}",
        LINE,
        f"🆚 <b>{e(m['opponent'])}</b>  ·  {size} vs {size}",
        f"👕 Kit: {e(m['kits'])}",
        LINE,
    ]
    if m["view"] == "attend":
        lines.append(f"✅ <b>ATTENDING</b>   {len(yes)}")
        if yes:
            lines += [f"{i}. {e(n)}" for i, n in enumerate(yes, 1)]
        else:
            lines.append("<i>No one yet. Be the first!</i>")
        lines.append("")
        lines.append(f"❌ Not attending: {len(no)}")
    else:
        lines.append(f"❌ <b>NOT ATTENDING</b>   {len(no)}")
        if no:
            lines += [f"{i}. {e(n)}" for i, n in enumerate(no, 1)]
        else:
            lines.append("<i>No one. Great!</i>")
        lines.append("")
        lines.append(f"✅ Attending: {len(yes)}")
    lines.append(LINE)
    if not m["open"]:
        lines.append("🔒 <b>VOTING CLOSED</b>")
    else:
        lines.append("<i>Tap a button below, or use /attend · /notattend · /change</i>")
    return "\n".join(lines)


def keyboard(m):
    if not m["open"]:
        return None
    votes = get_votes(m["id"])
    yes = sum(v["status"] == "ATTEND" for v in votes)
    no = sum(v["status"] == "NOT" for v in votes)
    show = "❌ Not attending" if m["view"] == "attend" else "✅ Attending"
    return Markup(
        [
            [
                Btn(f"✅ Attend ({yes})", callback_data=f"v:{m['id']}:ATTEND"),
                Btn(f"❌ Can't ({no})", callback_data=f"v:{m['id']}:NOT"),
            ],
            [Btn(f"👀 Show: {show}", callback_data=f"t:{m['id']}")],
        ]
    )


async def refresh(bot, mid):
    m = get_match(mid)
    try:
        await bot.edit_message_text(
            chat_id=m["chat_id"],
            message_id=m["message_id"],
            text=render(m, get_votes(mid)),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard(m),
        )
    except BadRequest as ex:
        if "not modified" not in str(ex).lower():
            raise


async def cast(bot, mid, user, status):
    """Record a vote. Returns False if nothing changed."""
    with db() as c:
        row = c.execute(
            "SELECT status FROM votes WHERE match_id=? AND user_id=?", (mid, user.id)
        ).fetchone()
        if row and row["status"] == status:
            return False
        c.execute(
            """INSERT INTO votes(match_id,user_id,name,status,updated)
               VALUES(?,?,?,?,strftime('%Y-%m-%d %H:%M:%f','now'))
                   ON CONFLICT(match_id,user_id) DO UPDATE SET
                status=excluded.status, name=excluded.name, updated=excluded.updated""",
            (mid, user.id, user.full_name, status),
        )
    await refresh(bot, mid)
    return True


# ------------------------------------------------- voting: buttons/commands
async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split(":")
    m = get_match(int(parts[1]))
    if not m or not m["open"]:
        await q.answer("This match is closed.", show_alert=True)
        return
    if parts[0] == "v":
        changed = await cast(ctx.bot, m["id"], q.from_user, parts[2])
        label = "Attending ✅" if parts[2] == "ATTEND" else "Not attending ❌"
        await q.answer(f"You are: {label}" if changed else f"Already {label}")
    else:  # toggle view (shared for everyone in the group)
        new = "not" if m["view"] == "attend" else "attend"
        with db() as c:
            c.execute("UPDATE matches SET view=? WHERE id=?", (new, m["id"]))
        await refresh(ctx.bot, m["id"])
        await q.answer()


async def _cmd_vote(update: Update, ctx: ContextTypes.DEFAULT_TYPE, status):
    m = latest_open(update.effective_chat.id)
    if not m:
        await update.message.reply_text("No open match. Create one with /newmatch")
        return
    user = update.effective_user
    if status == "FLIP":
        row = next((v for v in get_votes(m["id"]) if v["user_id"] == user.id), None)
        status = "NOT" if row and row["status"] == "ATTEND" else "ATTEND"
    await cast(ctx.bot, m["id"], user, status)
    try:  # keep the group clean (needs delete rights; ignore if missing)
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
    member = await chat.get_member(update.effective_user.id)
    if member.status not in ("administrator", "creator"):
        await update.message.reply_text("Only group admins can close a match.")
        return
    m = latest_open(chat.id)
    if not m:
        await update.message.reply_text("No open match.")
        return
    with db() as c:
        c.execute("UPDATE matches SET open=0 WHERE id=?", (m["id"],))
    await refresh(ctx.bot, m["id"])
    try:
        await ctx.bot.unpin_chat_message(chat.id, m["message_id"])
    except TelegramError:
        pass


# ------------------------------------------------------- /newmatch wizard
async def newmatch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("Please run /newmatch inside your team group.")
        return ConversationHandler.END
    ctx.user_data["m"] = {}
    await update.message.reply_text("📅 Match date? (e.g. Sat 10 Oct 2026)\n/cancel to stop")
    return DATE


def text_step(key, next_prompt, next_state):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        ctx.user_data["m"][key] = update.message.text.strip()
        await update.message.reply_text(next_prompt)
        return next_state

    return handler


async def got_end(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["m"]["end"] = update.message.text.strip()
    kb = Markup(
        [
            [Btn("7 vs 7", callback_data="sz:7"), Btn("9 vs 9", callback_data="sz:9")],
            [Btn("10 vs 10", callback_data="sz:10"), Btn("Custom", callback_data="sz:custom")],
        ]
    )
    await update.message.reply_text("👥 Team size?", reply_markup=kb)
    return SIZE


async def got_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    val = q.data.split(":")[1]
    if val == "custom":
        await q.message.reply_text("Type players per side (e.g. 8):")
        return CUSTOM
    ctx.user_data["m"]["size"] = int(val)
    await q.message.reply_text("📍 Location?")
    return LOCATION


async def got_custom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or not 2 <= int(txt) <= 15:
        await update.message.reply_text("Please send a number between 2 and 15.")
        return CUSTOM
    ctx.user_data["m"]["size"] = int(txt)
    await update.message.reply_text("📍 Location?")
    return LOCATION


async def got_kits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["m"]["kits"] = update.message.text.strip()
    m = {**ctx.user_data["m"], "view": "attend", "open": 1}
    kb = Markup([[Btn("✅ Confirm & post", callback_data="ok"), Btn("✖ Cancel", callback_data="cancel")]])
    await update.message.reply_text(
        "Preview:\n\n" + render(m, []), parse_mode=ParseMode.HTML, reply_markup=kb
    )
    return CONFIRM


async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = ctx.user_data.pop("m")
    chat_id = q.message.chat_id
    with db() as c:
        cur = c.execute(
            "INSERT INTO matches(chat_id,date,start,end,size,location,opponent,kits) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (chat_id, d["date"], d["start"], d["end"], d["size"], d["location"], d["opponent"], d["kits"]),
        )
        mid = cur.lastrowid
    m = get_match(mid)
    msg = await ctx.bot.send_message(
        chat_id, render(m, []), parse_mode=ParseMode.HTML, reply_markup=keyboard(m)
    )
    with db() as c:
        c.execute("UPDATE matches SET message_id=? WHERE id=?", (msg.message_id, mid))
    try:
        await ctx.bot.pin_chat_message(chat_id, msg.message_id)
    except TelegramError:
        await ctx.bot.send_message(chat_id, "⚠️ I couldn't pin it. Give me the 'Pin messages' admin right.")
    await q.message.edit_text("✅ Posted and pinned.")
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("m", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("Cancelled.")
    else:
        await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Match bot\n"
        "/newmatch – create a match poll (pinned)\n"
        "/attend  /notattend  /change – vote or change your vote\n"
        "/close – close voting (admins)"
    )


# -------------------------------------------------------------------- main
def main():
    init_db()
    app = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    txt = filters.TEXT & ~filters.COMMAND

    wizard = ConversationHandler(
        entry_points=[CommandHandler("newmatch", newmatch)],
        states={
            DATE: [MessageHandler(txt, text_step("date", "⏰ Start time? (e.g. 17:00)", START))],
            START: [MessageHandler(txt, text_step("start", "⏰ End time? (e.g. 19:00)", END))],
            END: [MessageHandler(txt, got_end)],
            SIZE: [CallbackQueryHandler(got_size, pattern=r"^sz:")],
            CUSTOM: [MessageHandler(txt, got_custom)],
            LOCATION: [MessageHandler(txt, text_step("location", "🆚 Opponent team name?", OPPONENT))],
            OPPONENT: [MessageHandler(txt, text_step("opponent", "👕 Kits? (e.g. Red jersey)", KITS))],
            KITS: [MessageHandler(txt, got_kits)],
            CONFIRM: [
                CallbackQueryHandler(confirm, pattern=r"^ok$"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600,
    )
    app.add_handler(wizard)
    app.add_handler(CallbackQueryHandler(on_button, pattern=r"^(v|t):"))
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("attend", cmd_attend))
    app.add_handler(CommandHandler("notattend", cmd_notattend))
    app.add_handler(CommandHandler("change", cmd_change))
    app.add_handler(CommandHandler("close", cmd_close))
    app.run_polling()


if __name__ == "__main__":
    main()