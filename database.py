import sqlite3

DB_PATH = "db.sqlite3"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT UNIQUE,
        tickets INTEGER DEFAULT 1,
        referrals INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ebook_id INTEGER,
        amount REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

def calc_referral_bonus(referrals):
    if referrals >= 100:
        return 300
    elif referrals >= 50:
        return 100
    elif referrals >= 25:
        return 40
    elif referrals >= 10:
        return 15
    elif referrals >= 5:
        return 5
    return 0
