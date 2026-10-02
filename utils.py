import html
import re
import asyncio
import unicodedata
import urllib.parse
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

from database import get_lang, get_match, get_votes
from strings import STR, FIELD_LABELS, t, pick

logger = logging.getLogger(__name__)

LINE = "━━━━━━━━━━━━━━━━━━"
e = html.escape

ALIASES = {
    "date": "date", "day": "date", "កាលបរិច្ឆេទ": "date", "ថ្ងៃ": "date",
    "start": "start", "from": "start", "ម៉ោងចាប់ផ្តើម": "start",
    "end": "end", "to": "end", "ម៉ោងបញ្ចប់": "end",
    "team": "size", "size": "size", "players": "size", "ក្រុម": "size",
    "location": "location", "place": "location", "field": "location",
    "venue": "location", "ទីតាំង": "location",
    "opponent": "opponent", "vs": "opponent", "against": "opponent",
    "ក្រុមគូប្រជែង": "opponent",
    "kit": "kits", "kits": "kits", "ឈុតអាវ": "kits",
}
REQUIRED = ["date", "start", "end", "size", "location", "opponent", "kits"]
KH_DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")


def get_val(obj, key, default=None):
    """Safely retrieves property whether obj is a dict or a SQLModel object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

async def delete_after(bot, chat_id: int, message_id: int, delay_seconds: int = 0):
    """Deletes a message after a given delay in seconds (default is instant)."""
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass

def get_display_width(text: str) -> int:
    """Calculate visible width of text, accounting for wide Unicode characters."""
    width = 0
    for char in text:
        # Strip zero-width joiners / non-spacing marks (common in Khmer script)
        if unicodedata.category(char) in ('Mn', 'Me', 'Cf'):
            continue
        # East Asian Wide / Fullwidth characters count as 2 width units
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width

def render(m, votes, lang: str = "km") -> str:
    yes = [get_val(v, "name") for v in votes if get_val(v, "status") == "ATTEND"]
    no = [get_val(v, "name") for v in votes if get_val(v, "status") == "NOT"]

    size = get_val(m, "size")
    total_spots = int(size) * 2 if size and str(size).isdigit() else None

    # 📍 Location Hyperlink Logic
    raw_loc = get_val(m, "location") or ""
    loc_url = get_val(m, "location_url")

    # Fallback: Auto-generate Google Maps search link if no direct URL was provided
    if not loc_url and raw_loc:
        encoded_query = urllib.parse.quote(raw_loc)
        loc_url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

    loc_display = f'<a href="{loc_url}">{e(raw_loc)}</a>' if loc_url else e(raw_loc)

    title_text = f"🏆  {t(lang, 'title')}  🏆"

    # 1. Calculate dynamic box width based on title content
    title_width = get_display_width(title_text)
    box_inner_width = max(title_width + 4, 28)  # Ensure a minimum clean width

    # Dynamic border components
    # top_border = "┌" + "─" * box_inner_width + "┐"
    # bottom_border = "└" + "─" * box_inner_width + "┘"
    dynamic_line = "─" * (box_inner_width + 2)

    # # Center title dynamically
    # padding = box_inner_width - title_width
    # left_pad = padding // 2
    # right_pad = padding - left_pad
    # centered_title = f"│{' ' * left_pad}{title_text}{' ' * right_pad}│"

    # Assemble Render Lines
    lines = [
        f"🏆 <b><i>  {t(lang, 'title')} </i></b> 🏆",
        f"📅 <b>{t(lang, 'date_label')}:</b> {e(get_val(m, 'date'))}",
        f"⏰ <b>{t(lang, 'time_label')}:</b> {e(get_val(m, 'start'))} - {e(get_val(m, 'end'))}",
        f"📍 <b>{t(lang, 'location_label')}:</b> {loc_display}",
        f"<code>{dynamic_line}</code>",

        f"⚔️ <b>{t(lang, 'vs_label')}:</b> {e(get_val(m, 'opponent'))}",
        f"⚽ <b>{t(lang, 'mode_label')}:</b> {size} vs {size}",
        f"👕 <b>{t(lang, 'kit_label')}:</b> {e(get_val(m, 'kits'))}",
        f"<code>{dynamic_line}</code>",
    ]

    # Dynamic Roster Section
    view = get_val(m, "view")
    if view == "attend":
        capacity_str = f"({len(yes)}"
        lines.append(f"✅ <b>{t(lang, 'attending')} {capacity_str}</b>")
        if yes:
            lines.extend([f"  {i}. {e(n)}" for i, n in enumerate(yes, 1)])
        else:
            lines.append(f"  <i>{t(lang, 'no_yes')}</i>")
        lines.append("")
        lines.append(f"❌ <b>{t(lang, 'count_no')}:</b> {len(no)}")
    else:
        lines.append(f"❌ <b>{t(lang, 'not_attending')} ({len(no)})</b>")
        if no:
            lines.extend([f"  {i}. {e(n)}" for i, n in enumerate(no, 1)])
        else:
            lines.append(f"  <i>{t(lang, 'no_no')}</i>")
        lines.append("")
        lines.append(f"✅ <b>{t(lang, 'count_yes')}:</b> {len(yes)}")

    # Footer Status
    lines.append(f"<code>{dynamic_line}</code>")
    if not get_val(m, "open"):
        lines.append(f"🔒 <b>{t(lang, 'closed')}</b>")
    else:
        lines.append(f"⚠️ <i>{t(lang, 'footer')}</i>")

    return "\n".join(lines)


def keyboard(m):
    if not get_val(m, "open"):
        return None

    chat_id = get_val(m, "chat_id")
    match_id = get_val(m, "id")
    view = get_val(m, "view")

    lang = get_lang(chat_id)
    votes = get_votes(match_id)

    yes = sum(get_val(v, "status") == "ATTEND" for v in votes)
    no = sum(get_val(v, "status") == "NOT" for v in votes)

    emoji, key = ("❌", "count_no") if view == "attend" else ("✅", "count_yes")

    return Markup(
        [
            [
                Btn(f"✅ {t(lang, 'btn_yes')} ({yes})", callback_data=f"v:{match_id}:ATTEND"),
                Btn(f"❌ {t(lang, 'btn_no')} ({no})", callback_data=f"v:{match_id}:NOT"),
            ],
            [Btn(f" {t(lang, 'see_text')} 👀 {emoji} {t(lang, key)}", callback_data=f"t:{match_id}")],
        ]
    )


async def refresh(bot, mid: int):
    m = get_match(mid)
    if not m:
        return

    chat_id = get_val(m, "chat_id")
    message_id = get_val(m, "message_id")

    if not message_id:
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=render(m, get_votes(mid), get_lang(chat_id)),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard(m),
        )
    except BadRequest as ex:
        if "not modified" not in str(ex).lower():
            raise


async def is_admin(bot, chat_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


def parse_form(text: str):
    data = {}
    for line in text.splitlines():
        parts = re.split(r"[:៖]", line, maxsplit=1)
        if len(parts) < 2:
            continue
        key = ALIASES.get(parts[0].strip().lower())
        value = parts[1].strip()
        if key and value:
            data[key] = value
    if "size" in data:
        found = re.search(r"\d+", data["size"].translate(KH_DIGITS))
        n = int(found.group()) if found else 0
        if 2 <= n <= 15:
            data["size"] = n
        else:
            del data["size"]
    return data, [k for k in REQUIRED if k not in data]

async def delete_job_callback(context: ContextTypes.DEFAULT_TYPE):
    """Callback triggered by JobQueue to delete a user's command message."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Auto-deleted command message {message_id} in chat {chat_id}")
    except BadRequest as ex:
        # Handles "Message to delete not found", "Message can't be deleted", etc.
        logger.debug(f"Could not auto-delete message {message_id}: {ex.message}")
    except Exception as ex:
        logger.warning(f"Unexpected error deleting message {message_id}: {ex}")


def schedule_command_deletion(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int = 900):
    """
    Schedules auto-deletion for user/admin commands.
    Default delay: 900 seconds = 15 minutes.
    For 1 hour, use delay_seconds = 3600.
    """
    context.job_queue.run_once(
        delete_job_callback,
        when=delay_seconds,
        data={"chat_id": chat_id, "message_id": message_id},
        name=f"auto_del_cmd_{chat_id}_{message_id}",
    )

async def clean(bot, chat_id: int, ids: list):
    for i in ids:
        try:
            await bot.delete_message(chat_id, i)
        except TelegramError:
            pass