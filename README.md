# ⚽ Telegram Match Attendance Bot

An English & Khmer dual-language Telegram bot built with `python-telegram-bot` (v21+) and `SQLModel` / `SQLAlchemy` to coordinate match availability, RSVP tracking, and squad management in group chats.
---

## 🛠 Features

* **Multi-Language Support**: English, Khmer (ខ្មែរ), or Dual-language mode (default).
* **Interactive Form Wizard**: Guided `/newmatch` creation with instant group preview.
* **Inline Voting & Real-Time Updating**: Attendees click dynamic buttons; the pinned match summary edits live without chat spam.
* **Database Agnostic**: Powered by `SQLModel` (SQLAlchemy ORM). Works out-of-the-box with **SQLite**, **PostgreSQL**, **MySQL**, or **MariaDB** by simply updating the `DATABASE_URL` environment variable.
* **Auto-Cleanup**: Cleans up wizard setup messages to keep group chats clutter-free.

---

## 📁 Project Structure

```text
match_bot/
├── .env                  # Bot credentials & DB URL (excluded from git)
├── config.py             # Global constants & environment variables
├── database.py           # SQLModel schema models & database engine
├── strings.py            # Dual-language translations (English / Khmer)
├── utils.py              # Parsing, message rendering & Telegram helpers
├── handlers/
│   ├── __init__.py       # Package marker
│   ├── general.py        # /start, /help, /lang commands & language toggling
│   ├── voting.py         # /attend, /notattend, /change, /close & inline buttons
│   └── match_wizard.py   # /newmatch conversation flow & setup preview
├── requirements.txt      # Project dependencies
└── main.py               # Bot entrypoint & handler registration
```

## ⚙️ Setup & Installation

Follow these steps to set up, configure, and run the bot on your server or local machine.

### 1. Prerequisites
* Python 3.10 or higher
* Git

### 2. Get a Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to create your bot.
3. Copy the **HTTP API Token** provided by BotFather.

### 3. Configure Bot Privileges (Crucial)
1. In [@BotFather](https://t.me/BotFather), send `/setprivacy`.
2. Select your newly created bot.
3. Choose **Disable**. *(This enables the bot to read form submission replies in group chats).*

### 4. Clone & Install
Clone the repository and install the dependencies:

```bash
git clone [https://github.com/your-username/match-attendance-bot.git](https://github.com/your-username/match-attendance-bot.git)
cd match-attendance-bot

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a .env file in the project root directory:

```bash
BOT_TOKEN=123456:ABC...

# Option A: SQLite (Local file)
DATABASE_URL=sqlite:///matches.db

# Option B: PostgreSQL
# DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/match_bot_db

# Option C: MySQL / MariaDB
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/match_bot_db
```

### 6. Group Setup
1. Add the bot to your team group chat.
2. Promote the bot to Administrator with the following permissions:
    * Delete messages (to remove wizard setup prompts)
    * Pin messages (to pin active match announcements)

### 7. Run the Bot Locally
```bash
python main.py
```