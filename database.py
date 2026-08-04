# database.py
# SQLAlchemy-based DB layer that works with SQLite (local) and PostgreSQL (Railway).
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
        g = session.query(Giveaway).get(1)
        if not g:
            g = Giveaway(id=1, active=0, pool_usd=0.0, entry_cost_tickets=10)
            session.add(g)
            session.commit()
    finally:
        session.close()


def get_session():
    return SessionLocal()

# helper to convert ORM row to dict similar to previous row_to_dict
def row_to_dict(obj):
    if obj is None:
        return None
    if hasattr(obj, "__dict__"):
        d = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return d
    return dict(obj)
