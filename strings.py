# Each entry is (English, Khmer)
STR = {
    "title": ("MATCH DAY", "ថ្ងៃប្រកួត"),
    "kit": ("Kit", "ឈុតអាវ"),
    "attending": ("ATTENDING", "មកចូលរួម"),
    "not_attending": ("NOT ATTENDING", "មិនមក"),
    "count_yes": ("Attending", "មកចូលរួម"),
    "count_no": ("Not attending", "មិនមក"),
    "no_yes": ("No one yet. Be the first!", "មិនទាន់មានអ្នកណាទេ។"),
    "no_no": ("No one. Great!", "គ្មានទេ។"),
    "closed": ("VOTING CLOSED", "បិទការចុះឈ្មោះហើយ"),
    "footer": (
        "Tap a button below, or use /attend · /notattend · /change",
        "ចុចប៊ូតុងខាងក្រោម ឬប្រើ /attend · /notattend · /change",
    ),
    "btn_yes": ("Attend", "មក"),
    "btn_no": ("Can't", "មិនមក"),
    "btn_confirm": ("✅ Confirm & post", "✅ បញ្ជាក់ & បង្ហោះ"),
    "btn_cancel": ("✖ Cancel", "✖ បោះបង់"),
    "you_yes": ("You are attending ✅", "អ្នកនឹងមក ✅"),
    "you_no": ("You are not attending ❌", "អ្នកមិនមកទេ ❌"),
    "already_yes": ("Already attending ✅", "អ្នកបានចុះឈ្មោះមករួចហើយ ✅"),
    "already_no": ("Already not attending ❌", "អ្នកបានប្រាប់ថាមិនមករួចហើយ ❌"),
    "closed_alert": ("This match is closed.", "ការប្រកួតនេះបានបិទហើយ។"),
    "no_open": (
        "No open match. Create one with /newmatch",
        "មិនមានការប្រកួតដែលកំពុងបើកទេ។ បង្កើតថ្មីដោយ /newmatch",
    ),
    "only_admin": (
        "Only group admins can do this.",
        "មានតែអ្នកគ្រប់គ្រងក្រុមប៉ុណ្ណោះដែលអាចធ្វើបាន។",
    ),
    "form_title": ("New match form", "ទម្រង់ប្រកួតថ្មី"),
    "form_help": (
        "Tap the form to copy it, fill it in, and send it back as ONE message:",
        "ចុចលើទម្រង់ដើម្បីចម្លង បំពេញ រួចផ្ញើមកវិញជាសារតែមួយ៖",
    ),
    "preview": ("Preview:", "មើលជាមុន៖"),
    "missing": ("Missing or invalid:", "ខ្វះ ឬមិនត្រឹមត្រូវ៖"),
    "resend": ("Please send the whole form again.", "សូមផ្ញើទម្រង់ទាំងមូលម្តងទៀត។"),
}

LONG_KEYS = {"footer", "form_help", "resend"}

FIELD_LABELS = {
    "date": ("Date", "កាលបរិច្ឆេទ"),
    "start": ("Start", "ម៉ោងចាប់ផ្តើម"),
    "end": ("End", "ម៉ោងបញ្ចប់"),
    "size": ("Team (a number, e.g. 7)", "ក្រុម (ជាលេខ ឧ. 7)"),
    "location": ("Location", "ទីតាំង"),
    "opponent": ("Opponent", "ក្រុមគូប្រជែង"),
    "kits": ("Kit", "ឈុតអាវ"),
}

HELP_TEXT = (
    "⚽ Match bot\n"
    "/newmatch – create a match / បង្កើតការប្រកួត\n"
    "/attend – I'm coming / ខ្ញុំមក\n"
    "/notattend – I can't come / ខ្ញុំមិនមក\n"
    "/change – change my answer / ប្តូរចម្លើយ\n"
    "/close – close voting (admins) / បិទការចុះឈ្មោះ (admin)\n"
    "/lang – language (admins) / ភាសា (admin)"
)

TEMPLATES = {
    "en": "Date: \nStart: \nEnd: \nTeam: 7\nLocation: \nOpponent: \nKit: ",
    "km": "កាលបរិច្ឆេទ: \nម៉ោងចាប់ផ្តើម: \nម៉ោងបញ្ចប់: \nក្រុម: 7\nទីតាំង: \nក្រុមគូប្រជែង: \nឈុតអាវ: ",
}


def pick(lang: str, pair: tuple, sep: str = " / ") -> str:
    en, km = pair
    if lang == "km":
        return km
    if lang == "both":
        return f"{en}{sep}{km}"
    return en


def t(lang: str, key: str) -> str:
    return pick(lang, STR[key], "\n" if key in LONG_KEYS else " / ")