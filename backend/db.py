"""Database access for the course explorer.

One SQLAlchemy engine for the whole backend. Locally it uses data/yale_som.db
(SQLite). Set DATABASE_URL (e.g. a Supabase Postgres connection string) to point
the app somewhere else — no other code changes needed.

Tables
- courses: the SOM catalog (already in yale_som.db; read-only here)
- users:   one row per account (email + bcrypt password hash)
- chats:   one row per chat exchange (user message, agent reply, tools used)
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    select,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

DEFAULT_DB_URL = f"sqlite:///{(ROOT / 'data' / 'yale_som.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or DEFAULT_DB_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()

courses = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("course_id", Text),
    Column("course_number", Text),
    Column("course_title", Text),
    Column("course_category", Text),
    Column("course_type", Text),
    Column("course_session", Text),
    Column("course_description", Text),
    Column("faculty_1", Text),
    Column("faculty_1_email", Text),
    Column("faculty_bio", Text),
    Column("daytimes", Text),
    Column("timings_day", Text),
    Column("timings_start", Text),
    Column("timings_end", Text),
    Column("room", Text),
    Column("section", Text),
    Column("units", Text),
    Column("term_code", Text),
    Column("syllabus", Text),
    Column("old_syllabus", Text),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("password_hash", String(100), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

chats = Table(
    "chats",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("message", Text, nullable=False),
    Column("reply", Text, nullable=False),
    Column("tools_used", Text, nullable=False, default="[]"),  # JSON list of tool names
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


def init_db() -> None:
    """Create any missing tables. Existing tables (and their rows) are left alone."""
    metadata.create_all(engine, checkfirst=True)


def fetch_courses() -> list[dict]:
    """All courses as plain dicts (snake_case columns), in catalog order."""
    with engine.connect() as conn:
        rows = conn.execute(select(courses).order_by(courses.c.id)).mappings().all()
    return [dict(row) for row in rows]
