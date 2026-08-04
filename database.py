import sqlite3
import json
from contextlib import closing
from pathlib import Path

DB_PATH = Path("data.sqlite3")


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn=None):
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    with closing(conn.cursor()) as cur:
        # users: telegram_id primary key
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            tickets INTEGER NOT NULL DEFAULT 0,
            referrals INTEGER NOT NULL DEFAULT 0,
            ebooks_owned TEXT DEFAULT '[]',
            ref_bonus_level INTEGER NOT NULL DEFAULT 0
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT NOT NULL,
            referred_id TEXT NOT NULL,
            UNIQUE(referrer_id, referred_id)
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS ebooks (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            title TEXT NOT NULL,
            price_usd REAL NOT NULL,
            tickets_awarded INTEGER NOT NULL
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS giveaway (
            id INTEGER PRIMARY KEY CHECK (id=1),
            active INTEGER NOT NULL DEFAULT 0,
            pool_usd REAL NOT NULL DEFAULT 0,
            entry_cost_tickets INTEGER NOT NULL DEFAULT 10
        )
        """
        )
        # create single row default for giveaway
        cur.execute("INSERT OR IGNORE INTO giveaway (id, active, pool_usd, entry_cost_tickets) VALUES (1,0,0,10)")
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS giveaway_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT NOT NULL,
            entries INTEGER NOT NULL DEFAULT 1
        )
        """
        )
        conn.commit()
    if close_conn:
        conn.close()


def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # convert JSON columns
    if "ebooks_owned" in d and isinstance(d["ebooks_owned"], str):
        try:
            d["ebooks_owned"] = json.loads(d["ebooks_owned"])
        except Exception:
            d["ebooks_owned"] = []
    return d
