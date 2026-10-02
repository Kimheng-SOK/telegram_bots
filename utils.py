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


def render(m, votes, lang: str) -> str:
    yes = [v["name"] for v in votes if v["status"] == "ATTEND"]
    no = [v["name"] for v in votes if v["status"] == "NOT"]
    size = m["size"]
    lines = [
        f"⚽ <b>{t(lang, 'title')}</b> ⚽",
        LINE,
        f"📅 <b>{e(m['date'])}</b>",
        f"⏰ {e(m['start'])} – {e(m['end'])}",
        f"📍 {e(m['location'])}",
        LINE,
        f"🆚 <b>{e(m['opponent'])}</b>  ·  {size} vs {size}",
        f"👕 {t(lang, 'kit')}: {e(m['kits'])}",
        LINE,
    ]
    if m["view"] == "attend":
        lines.append(f"✅ <b>{t(lang, 'attending')}</b>   {len(yes)}")
        if yes:
            lines += [f"{i}. {e(n)}" for i, n in enumerate(yes, 1)]
        else:
            lines.append(f"<i>{t(lang, 'no_yes')}</i>")
        lines.append("")
        lines.append(f"❌ {t(lang, 'count_no')}: {len(no)}")
    else:
        lines.append(f"❌ <b>{t(lang, 'not_attending')}</b>   {len(no)}")
        if no:
            lines += [f"{i}. {e(n)}" for i, n in enumerate(no, 1)]
        else:
            lines.append(f"<i>{t(lang, 'no_no')}</i>")
        lines.append("")
        lines.append(f"✅ {t(lang, 'count_yes')}: {len(yes)}")
    lines.append(LINE)
    if not m["open"]:
        lines.append(f"🔒 <b>{t(lang, 'closed')}</b>")
    else:
        lines.append(f"<i>{t(lang, 'footer')}</i>")
    return "\n".join(lines)


def keyboard(m):
    if not m["open"]:
        return None
    lang = get_lang(m["chat_id"])
    votes = get_votes(m["id"])
    yes = sum(v["status"] == "ATTEND" for v in votes)
    no = sum(v["status"] == "NOT" for v in votes)
    emoji, key = ("❌", "count_no") if m["view"] == "attend" else ("✅", "count_yes")
    return Markup(
        [
            [
                Btn(f"✅ {t(lang, 'btn_yes')} ({yes})", callback_data=f"v:{m['id']}:ATTEND"),
                Btn(f"❌ {t(lang, 'btn_no')} ({no})", callback_data=f"v:{m['id']}:NOT"),
            ],
            [Btn(f"👀 {emoji} {t(lang, key)}", callback_data=f"t:{m['id']}")],
        ]
    )


async def refresh(bot, mid: int):
    m = get_match(mid)
    try:
        await bot.edit_message_text(
            chat_id=m["chat_id"],
            message_id=m["message_id"],
            text=render(m, get_votes(mid), get_lang(m["chat_id"])),
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