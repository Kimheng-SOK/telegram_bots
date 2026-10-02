import sqlite3
from config import DB_FILE, DEFAULT_LANG


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


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
            CREATE TABLE IF NOT EXISTS chats(chat_id INTEGER PRIMARY KEY, lang TEXT);
            """
        )


def get_lang(chat_id: int) -> str:
    with db() as c:
        row = c.execute("SELECT lang FROM chats WHERE chat_id=?", (chat_id,)).fetchone()
    return row["lang"] if row else DEFAULT_LANG


def set_lang(chat_id: int, lang: str):
    with db() as c:
        c.execute(
            "INSERT INTO chats(chat_id,lang) VALUES(?,?) "
            "ON CONFLICT(chat_id) DO UPDATE SET lang=excluded.lang",
            (chat_id, lang),
        )


def get_match(mid: int):
    with db() as c:
        return c.execute("SELECT * FROM matches WHERE id=?", (mid,)).fetchone()


def latest_open(chat_id: int):
    with db() as c:
        return c.execute(
            "SELECT * FROM matches WHERE chat_id=? AND open=1 AND message_id IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (chat_id,),
        ).fetchone()


def get_votes(mid: int):
    with db() as c:
        return c.execute(
            "SELECT * FROM votes WHERE match_id=? ORDER BY updated, rowid", (mid,)
        ).fetchall()


def create_match(chat_id: int, data: dict) -> int:
    with db() as c:
        cur = c.execute(
            "INSERT INTO matches(chat_id,date,start,end,size,location,opponent,kits) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                chat_id,
                data["date"],
                data["start"],
                data["end"],
                data["size"],
                data["location"],
                data["opponent"],
                data["kits"],
            ),
        )
        return cur.lastrowid


def update_match_message_id(mid: int, message_id: int):
    with db() as c:
        c.execute("UPDATE matches SET message_id=? WHERE id=?", (message_id, mid))


def set_match_view(mid: int, view: str):
    with db() as c:
        c.execute("UPDATE matches SET view=? WHERE id=?", (view, mid))


def close_match(mid: int):
    with db() as c:
        c.execute("UPDATE matches SET open=0 WHERE id=?", (mid,))


def record_vote(mid: int, user_id: int, user_full_name: str, status: str) -> bool:
    with db() as c:
        row = c.execute(
            "SELECT status FROM votes WHERE match_id=? AND user_id=?", (mid, user_id)
        ).fetchone()
        if row and row["status"] == status:
            return False
        c.execute(
            """INSERT INTO votes(match_id,user_id,name,status,updated)
               VALUES(?,?,?,?,strftime('%Y-%m-%d %H:%M:%f','now'))
                   ON CONFLICT(match_id,user_id) DO UPDATE SET
                status=excluded.status, name=excluded.name, updated=excluded.updated""",
            (mid, user_id, user_full_name, status),
        )
    return True