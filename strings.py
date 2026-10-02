# Each entry is either (English, Khmer) tuple or {"en": ..., "km": ...} dict
STR = {
    "title": ("friendly match", "ការប្រកួតបាល់ទាត់"),
    "date_label": ("Date", "កាលបរិច្ឆេទ"),
    "time_label": ("Time", "ពេលវេលា"),
    "location_label": ("Location", "ទីតាំង"),
    "vs_label": ("Opponent", "ប្រកួតជាមួយ"),
    "mode_label": ("Mode", "ទម្រង់លេង"),
    "kit_label": ("Kit", "ឯកសណ្ឋាន"),
    "attending": ("ATTENDING", "បានចូលរួម"),
    "not_attending": ("NOT ATTENDING", "មិនបានចូលរួម"),
    "count_yes": ("Attending", "អ្នកបានចូលរួម"),
    "count_no": ("Not attending", "អ្នកមិនចូលរួម"),
    "no_yes": ("No one yet. Be the first!", "មិនទាន់មានអ្នកណាចូលរួមទេ ចុចខាងក្រោមដើម្បីក្លាយជាមនុស្សទីមួយ🕺"),
    "no_no": ("No one. Great!", "គ្មានទេ។ ពិតជាគួរអោយរំភើបមែន🫨"),
    "closed": ("Voting has ended / Poll closed", "បិទការចុះឈ្មោះហើយ😎"),
    "footer": (
        "⏰ Please arrive 15–20 minutes early! Let's bring our A-game! 💪🔥",
        "⚡️ គោរពពេលវេលា = គោរពក្រុម!\n សូមមកដល់មុនម៉ោង ១៥នាទី ដើម្បីត្រៀមខ្លួន ⚽️🔥",
    ),
    "btn_yes": ("Attend", "បានទៅ"),
    "btn_no": ("Can't", "មិនបានទៅ"),
    "btn_confirm": ("✅ Confirm & post", "✅ បញ្ជាក់ & បង្ហោះ"),
    "btn_cancel": ("✖ Cancel", "✖ បោះបង់"),
    "you_yes": ("You are attending ✅", "🤩 អ្នកនឹងចូលរួម តែបើអត់មកទេ គុណលុយនឹង២ 🤩"),
    "you_no": ("You are not attending ❌", "👹 ប្រាកដហើយថាអត់មក ប្រយ័ត្នស្តាយក្រោយ 👹"),
    "already_yes": ("Already attending ✅", "🫶 អ្នកបានចុះឈ្មោះមករួចហើយ 🫶"),
    "already_no": ("Already not attending ❌", "🤌 អ្នកបានប្រាប់ថាមិនមករួចហើយ 🤌"),
    "closed_alert": ("This match is closed.", "ការប្រកួតនេះបានបិទហើយ។"),
    "see_text": ("Show", "មើល"),
    "no_open": {
        "en": "No open match. Create one with /newmatch",
        "km": "មិនមានការប្រកួតដែលកំពុងបើកទេ។ បង្កើតថ្មីដោយ /newmatch",
    },
    "form_title": ("New match form", "ទម្រង់ប្រកួតថ្មី"),
    "form_help": (
        "Tap the form to copy it, fill it in, and send it back as ONE message:",
        "ចុចលើទម្រង់ដើម្បីចម្លង បំពេញ រួចផ្ញើមកវិញជាសារតែមួយ៖",
    ),
    "preview": ("Preview:", "ផ្ទៀងផ្ទាត់៖"),
    "missing": ("Missing or invalid:", "ខ្វះ ឬមិនត្រឹមត្រូវ៖"),
    "resend": ("Please send the whole form again.", "សូមផ្ញើទម្រង់សារជាថ្មី។"),
    "select_lang": {
        "en": "🌐 Please select group language:",
        "km": "🌐 សូមជ្រើសរើសភាសាសម្រាប់ក្រុម៖",
    },
    "only_admin": {
        "en": "⚠️ Only group administrators can use this command.",
        "km": "⚠️ មានតែអ្នកគ្រប់គ្រងក្រុមប៉ុណ្ណោះដែលអានប្រើពាក្យបញ្ជានេះបាន។"
    },
    "no_match_found": {
        "en": "❌ No match found to reopen.",
        "km": "❌ មិនមានការប្រកួតសម្រាប់បើកឡើងវិញទេ។"
    },
    "reopen_prompt": {
        "en": "Click below to confirm reopening the match form:",
        "km": "ចុចខាងក្រោមដើម្បីបញ្ជាក់ការបើកទម្រង់ឡើងវិញ៖"
    },
    "btn_confirm_reopen": {
        "en": "🔓 Confirm Reopen",
        "km": "🔓 បញ្ជាក់ការបើកឡើងវិញ"
    },
    "alert_match_reopened": {
        "en": "🔓 The match form has been reopened successfully!",
        "km": "🔓 ទម្រង់ការប្រកួតត្រូវបានបើកឡើងវិញដោយជោគជ័យ!"
    },
    "alert_match_closed": {
        "en": "🔒 The match form is now closed.",
        "km": "🔒 ទម្រង់ការប្រកួតត្រូវបានបិទហើយ!"
    },
    "alert_already_open": {
        "en": "⚠️ This match form is already open.",
        "km": "⚠️ ទម្រង់ការប្រកួតនេះត្រូវបានបើករួចហើយ!"
    },
    "close_prompt": {
        "en": "Click below to confirm closing the match form:",
        "km": "ចុចខាងក្រោមដើម្បីបញ្ជាក់ការបិទទម្រង់៖",
    },
    "btn_confirm_close": {
        "en": "🔒 Confirm Close",
        "km": "🔒 បញ្ជាក់ការបិទ",
    },
    "alert_match_closed": {
        "en": "🔒 The match form is now closed.",
        "km": "🔒 ទម្រង់ការប្រកួតត្រូវបានបិទហើយ!",
    },
    "lang_updated": {
        "en": "✅ Language updated successfully!",
        "km": "✅ ភាសាត្រូវបានផ្លាស់ប្តូរដោយជោគជ័យ!",
    },
    "help_text": {
        "en": (
            "⚽ Match bot\n"
            "/newmatch – Create a new match announcement\n"
            "/close – [Admin] Close voting & unpin post\n"
            "/reopen - [Admin] Reopen voting post for latest close\n"
            "/lang – [Admin] Set group language\n"
            "/cancel – Cancel active match creation"
        ),
        "km": (
            "⚽ Match bot\n"
            "/newmatch – បង្កើតការប្រកួតថ្មី\n"
            "/close – បិទការចុះឈ្មោះ (សម្រាប់ admin)\n"
            "/reopen - បើកឡើងវិញនូវតារាងចុងក្រោយគេ (សម្រាប់ admin)\n"
            "/lang – ប្តូរភាសា (សម្រាប់ admin)\n"
            "/cancel – បោះបង់ការបង្កើត"
        ),
    },
    "form_title": {
        "en": "Create New Match Announcement",
        "km": "បង្កើតការប្រកួតថ្មី",
    },
    "form_help": {
        "en": "Copy the template below, replace with your match info, and reply to this message:",
        "km": "សូមចម្លងទម្រង់ខាងក្រោម កែប្រែព័ត៌មានតាមការប្រកួតរបស់អ្នក ហើយផ្ញើReplyសារនេះ៖",
    },
}

LONG_KEYS = {"footer", "form_help", "resend", "help_text"}

FIELD_LABELS = {
    "date": ("Date", "កាលបរិច្ឆេទ"),
    "start": ("Start", "ម៉ោងចាប់ផ្តើម"),
    "end": ("End", "ម៉ោងបញ្ចប់"),
    "size": ("Team (a number, e.g. 7)", "ក្រុម (ជាលេខ ឧ. 7)"),
    "location": ("Location", "ទីតាំងតារាង"),
    "opponent": ("Opponent", "ក្រុមគូប្រជែង"),
    "kits": ("Kit", "ឈុតអាវ"),
}

TEMPLATES = {
    "en": (
        "Date: Sunday 04.10.2026\n"
        "Start: 07:00 PM\n"
        "End: 09:00 PM\n"
        "Team: 10\n"
        "Location: Sokhak Sport Club\n"
        "Location URL: https://maps.google.com/?q=Sokhak+Sport+Club\n"
        "Opponent: រ៉ាដាសន្តិភាព\n"
        "Kit: Green"
    ),
    "km": (
        "កាលបរិច្ឆេទ: ថ្ងៃអាទិត្យ 04.10.2026\n"
        "ម៉ោងចាប់ផ្តើម: 07:00 PM\n"
        "ម៉ោងបញ្ចប់: 09:00 PM\n"
        "ក្រុម: 10\n"
        "ទីតាំង: Sokhak Sport Club\n"
        "តំណភ្ជាប់ទីតាំង: https://maps.google.com/?q=Sokhak+Sport+Club\n"
        "ក្រុមគូប្រជែង: រ៉ាដាសន្តិភាព\n"
        "ឈុតអាវ: ពណ៌បៃតង"
    ),
}


def pick(lang: str, pair: tuple, sep: str = " / ") -> str:
    en, km = pair
    if lang == "km":
        return km
    if lang == "both":
        return f"{en}{sep}{km}"
    return en


def t(lang: str, key: str) -> str:
    if key not in STR:
        return key

    val = STR[key]
    sep = "\n" if key in LONG_KEYS else " / "

    # Handle dictionary entries {"en": ..., "km": ...}
    if isinstance(val, dict):
        en_str = val.get("en", "")
        km_str = val.get("km", val.get("kh", ""))  # supports both 'km' and 'kh' fallback
        if lang == "km":
            return km_str
        if lang == "both":
            return f"{en_str}{sep}{km_str}"
        return en_str

    # Handle tuple entries ("English", "Khmer")
    if isinstance(val, tuple):
        return pick(lang, val, sep)

    return str(val)