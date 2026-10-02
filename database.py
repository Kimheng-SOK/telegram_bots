from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Session, create_engine, select

from config import DATABASE_URL, DEFAULT_LANG

# SQLite multi-thread safety check
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


# -------------------------------------------------------------------- Models
class Matches(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(index=True)
    message_id: Optional[int] = Field(default=None)
    date: str
    start: str
    end: str
    size: int
    location: str
    location_url: Optional[str] = Field(default=None)
    opponent: str
    kits: str
    view: str = Field(default="attend")
    open: int = Field(default=1)


class Votes(SQLModel, table=True):
    match_id: int = Field(primary_key=True)
    user_id: int = Field(primary_key=True)
    name: str
    status: str
    updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Chats(SQLModel, table=True):
    chat_id: int = Field(primary_key=True)
    lang: str


# ----------------------------------------------------------- DB Operations
def init_db():
    """Creates tables for whatever database engine DATABASE_URL points to."""
    SQLModel.metadata.create_all(engine)


def get_lang(chat_id: int) -> str:
    with Session(engine) as session:
        chat = session.get(Chats, chat_id)
        return chat.lang if chat else DEFAULT_LANG


def set_lang(chat_id: int, lang: str):
    with Session(engine) as session:
        chat = session.get(Chats, chat_id)
        if chat:
            chat.lang = lang
        else:
            chat = Chats(chat_id=chat_id, lang=lang)
            session.add(chat)
        session.commit()


def get_match(mid: int) -> Optional[Matches]:
    with Session(engine) as session:
        return session.get(Matches, mid)


def latest_open(chat_id: int) -> Optional[Matches]:
    with Session(engine) as session:
        statement = (
            select(Matches)
            .where(Matches.chat_id == chat_id)
            .where(Matches.open == 1)
            .where(Matches.message_id.is_not(None))
            .order_by(Matches.id.desc())
            .limit(1)
        )
        return session.exec(statement).first()


# In database.py
def get_match_by_id(mid: int) -> Optional[Matches]:
    """Retrieves a single match record by ID."""
    with Session(engine) as session:
        return session.get(Matches, mid)


def get_votes(mid: int) -> list[Votes]:
    with Session(engine) as session:
        statement = (
            select(Votes)
            .where(Votes.match_id == mid)
            .order_by(Votes.updated, Votes.user_id)
        )
        return session.exec(statement).all()


def create_match(chat_id: int, data: dict) -> int:
    with Session(engine) as session:
        match = Matches(
            chat_id=chat_id,
            date=data["date"],
            start=data["start"],
            end=data["end"],
            size=data["size"],
            location=data["location"],
            location_url=data.get("location_url"),
            opponent=data["opponent"],
            kits=data["kits"],
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        return match.id


def update_match_message_id(mid: int, message_id: int):
    with Session(engine) as session:
        match = session.get(Matches, mid)
        if match:
            match.message_id = message_id
            session.commit()


def set_match_view(mid: int, view: str):
    with Session(engine) as session:
        match = session.get(Matches, mid)
        if match:
            match.view = view
            session.commit()


def close_match(mid: int):
    with Session(engine) as session:
        match = session.get(Matches, mid)
        if match:
            match.open = 0
            session.commit()


def reopen_match(mid: int):
    """Reopens a match so users can vote again."""
    with Session(engine) as session:
        match = session.get(Matches, mid)
        if match:
            match.open = 1
            session.commit()


def get_latest_match(chat_id: int) -> Optional[Matches]:
    """Retrieves the most recent match for a chat regardless of status."""
    with Session(engine) as session:
        statement = (
            select(Matches)
            .where(Matches.chat_id == chat_id)
            .order_by(Matches.id.desc())
            .limit(1)
        )
        return session.exec(statement).first()


def record_vote(mid: int, user_id: int, user_full_name: str, status: str) -> bool:
    with Session(engine) as session:
        vote = session.get(Votes, (mid, user_id))
        now = datetime.now(timezone.utc)

        if vote:
            if vote.status == status:
                return False  # No status change
            vote.status = status
            vote.name = user_full_name
            vote.updated = now
        else:
            vote = Votes(
                match_id=mid,
                user_id=user_id,
                name=user_full_name,
                status=status,
                updated=now,
            )
            session.add(vote)
        session.commit()
        return True