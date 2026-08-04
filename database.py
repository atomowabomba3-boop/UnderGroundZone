# database.py
# SQLAlchemy-based DB layer that works with SQLite (local) and PostgreSQL (Railway).
# Also exposes a backwards-compatible `get_conn()` wrapper which returns a DB-API
# connection whose cursor() yields dict-like rows (so older sqlite-style code keeps working).

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE") or "sqlite:///data.sqlite3"

# If using file-based sqlite, ensure directory exists
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()

# Models (mirroring previous sqlite schema)
class User(Base):
    __tablename__ = "users"
    telegram_id = Column(String, primary_key=True, index=True)
    tickets = Column(Integer, nullable=False, default=0)
    referrals = Column(Integer, nullable=False, default=0)
    ebooks_owned = Column(Text, nullable=False, default="[]")  # keep JSON as text for compatibility
    ref_bonus_level = Column(Integer, nullable=False, default=0)


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(String, nullable=False)
    referred_id = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("referrer_id", "referred_id", name="uq_ref_pair"),)


class Ebook(Base):
    __tablename__ = "ebooks"
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price_usd = Column(Float, nullable=False)
    tickets_awarded = Column(Integer, nullable=False)


class Giveaway(Base):
    __tablename__ = "giveaway"
    id = Column(Integer, primary_key=True)
    active = Column(Integer, nullable=False, default=0)
    pool_usd = Column(Float, nullable=False, default=0.0)
    entry_cost_tickets = Column(Integer, nullable=False, default=10)
    __table_args__ = (CheckConstraint("id = 1", name="ck_giveaway_single_row"),)


class GiveawayParticipant(Base):
    __tablename__ = "giveaway_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, nullable=False)
    entries = Column(Integer, nullable=False, default=1)


def init_db():
    Base.metadata.create_all(bind=engine)
    # ensure single giveaway row (id=1)
    session = SessionLocal()
    try:
        g = session.get(Giveaway, 1)
        if not g:
            g = Giveaway(id=1, active=0, pool_usd=0.0, entry_cost_tickets=10)
            session.add(g)
            session.commit()
    finally:
        session.close()


def get_session():
    return SessionLocal()


# --- Backwards-compatible DB-API connection wrapper ---
# Many of the existing modules (api.py, utils.py, giveaway.py) expected a
# sqlite3.Connection with cursor()/execute()/fetchone() semantics and rows
# that are dict-like (sqlite3.Row). To avoid changing all call sites, expose
# `get_conn()` that returns either a sqlite3.Connection (with row_factory)
# or a small wrapper around a psycopg2 connection that returns RealDictCursor.


def _get_sqlite_conn(path):
    import sqlite3
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class _PGConnWrapper:
    def __init__(self, conn):
        # conn is a psycopg2 connection
        self._conn = conn

    def cursor(self):
        # return a cursor that yields dict-like rows
        import psycopg2.extras
        return self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_conn():
    """Return a DB-API connection compatible with earlier sqlite usage.

    - For sqlite (DATABASE or sqlite:///...), returns sqlite3.Connection with row_factory sqlite3.Row.
    - For Postgres (DATABASE_URL), returns a wrapper around psycopg2 connection whose
      cursor() yields dict-like rows (RealDictCursor).
    """
    if DATABASE_URL.startswith("sqlite:///"):
        path = DATABASE_URL.replace("sqlite:///", "")
        return _get_sqlite_conn(path)
    else:
        try:
            import psycopg2
        except Exception as e:
            raise RuntimeError("psycopg2 is required for Postgres DATABASE_URL") from e
        # psycopg2.connect accepts the full DATABASE_URL string
        conn = psycopg2.connect(DATABASE_URL)
        return _PGConnWrapper(conn)


# helper to convert ORM row or DB-API row to dict similar to previous row_to_dict

def row_to_dict(row):
    if row is None:
        return None
    # SQLAlchemy ORM object
    if hasattr(row, "__dict__") and not isinstance(row, (dict,)):
        d = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
        # keep ebooks_owned as list if possible
        if "ebooks_owned" in d and isinstance(d["ebooks_owned"], str):
            try:
                import json
                d["ebooks_owned"] = json.loads(d["ebooks_owned"])
            except Exception:
                pass
        return d
    # psycopg2 RealDictRow or sqlite3.Row or mapping
    try:
        if isinstance(row, dict):
            return row
        # sqlite3.Row implements mapping protocol
        return dict(row)
    except Exception:
        # fallback: convert by iterating attributes
        d = {}
        for attr in dir(row):
            if attr.startswith("_"):
                continue
            try:
                d[attr] = getattr(row, attr)
            except Exception:
                pass
        return d
