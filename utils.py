import html
import re
from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

from database import get_lang, get_match, get_votes
from strings import STR, FIELD_LABELS, t, pick

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


def render(m, votes, lang: str) -> str:
    yes = [get_val(v, "name") for v in votes if get_val(v, "status") == "ATTEND"]
    no = [get_val(v, "name") for v in votes if get_val(v, "status") == "NOT"]
    size = get_val(m, "size")

    lines = [
        f"⚽ <b>{t(lang, 'title')}</b> ⚽",
        LINE,
        f"📅 <b>{e(get_val(m, 'date'))}</b>",
        f"⏰ {e(get_val(m, 'start'))} – {e(get_val(m, 'end'))}",
        f"📍 {e(get_val(m, 'location'))}",
        LINE,
        f"🆚 <b>{e(get_val(m, 'opponent'))}</b>  ·  {size} vs {size}",
        f"👕 {t(lang, 'kit')}: {e(get_val(m, 'kits'))}",
        LINE,
    ]

    if get_val(m, "view") == "attend":
        lines.append(f"✅ <b>{t(lang, 'attending')}</b>   {len(yes)}")
        lines += [f"{i}. {e(n)}" for i, n in enumerate(yes, 1)] if yes else [f"<i>{t(lang, 'no_yes')}</i>"]
        lines.append("")
        lines.append(f"❌ {t(lang, 'count_no')}: {len(no)}")
    else:
        lines.append(f"❌ <b>{t(lang, 'not_attending')}</b>   {len(no)}")
        lines += [f"{i}. {e(n)}" for i, n in enumerate(no, 1)] if no else [f"<i>{t(lang, 'no_no')}</i>"]
        lines.append("")
        lines.append(f"✅ {t(lang, 'count_yes')}: {len(yes)}")

    lines.append(LINE)
    if not get_val(m, "open"):
        lines.append(f"🔒 <b>{t(lang, 'closed')}</b>")
    else:
        lines.append(f"<i>{t(lang, 'footer')}</i>")

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
            [Btn(f"👀 {emoji} {t(lang, key)}", callback_data=f"t:{match_id}")],
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


async def clean(bot, chat_id: int, ids: list):
    for i in ids:
        try:
            await bot.delete_message(chat_id, i)
        except TelegramError:
            pass