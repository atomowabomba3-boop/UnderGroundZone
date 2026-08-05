import sqlite3
import os
from datetime import datetime, timedelta
import json

DB_PATH = os.getenv('DATABASE_PATH') or os.getenv('DATABASE_URL') or 'data.db'

def _connect():
    # Support sqlite URL like sqlite:///data.db
    if DB_PATH.startswith('sqlite:///'):
        path = DB_PATH.replace('sqlite:///', '')
    else:
        path = DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)} if c.description else {}
    return conn

# Public helpers expected by the app
def get_db_connection():
    return _connect()

def init_db():
    conn = _connect()
    cur = conn.cursor()

    # users: id, telegram_id (unique), tickets (int), referrals_count (int), ebooks_owned (json)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            tickets INTEGER DEFAULT 0,
            referrals_count INTEGER DEFAULT 0,
            ebooks_owned TEXT DEFAULT '[]'
        )
    ''')

    # ebooks table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ebooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price_usd REAL
        )
    ''')

    # giveaway table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS giveaway (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_amount REAL,
            num_winners INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            ends_at TEXT,
            winner_id INTEGER,
            ended_at TEXT
        )
    ''')

    # participants
    cur.execute('''
        CREATE TABLE IF NOT EXISTS giveaway_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giveaway_id INTEGER,
            user_id INTEGER,
            tickets_spent INTEGER,
            UNIQUE(giveaway_id, user_id)
        )
    ''')

    # payout requests for winners
    cur.execute('''
        CREATE TABLE IF NOT EXISTS giveaway_payouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giveaway_id INTEGER,
            user_id INTEGER,
            currency TEXT,
            address TEXT,
            confirmed_at TEXT,
            UNIQUE(giveaway_id, user_id)
        )
    ''')

    conn.commit()
    conn.close()

# User helpers
def create_user(telegram_id):
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (telegram_id, tickets, referrals_count, ebooks_owned) VALUES (?, ?, ?, ?)',
                    (int(telegram_id), 0, 0, json.dumps([])))
        conn.commit()
        uid = cur.lastrowid
        cur.execute('SELECT * FROM users WHERE id = ?', (uid,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        conn.rollback()
        cur.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cur.fetchone()
        conn.close()
        return row

def get_user(telegram_id):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE telegram_id = ?', (int(telegram_id),))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = ?', (int(user_id),))
    row = cur.fetchone()
    conn.close()
    return row

def update_user_tickets(user_id, tickets):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('UPDATE users SET tickets = ? WHERE id = ?', (int(tickets), int(user_id)))
    conn.commit()
    conn.close()
    return True

# Referral
def add_referral(referrer_telegram_id, referred_telegram_id):
    try:
        ref = get_user(referrer_telegram_id)
        if not ref:
            # create referrer if missing
            ref = create_user(referrer_telegram_id)
        referred = get_user(referred_telegram_id)
        if not referred:
            referred = create_user(referred_telegram_id)
        conn = _connect()
        cur = conn.cursor()
        # Increment referrals_count and give 1 ticket to referrer
        cur.execute('UPDATE users SET referrals_count = referrals_count + 1, tickets = tickets + 1 WHERE telegram_id = ?', (int(referrer_telegram_id),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# Ranking
def get_ranking(limit=10):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT telegram_id, referrals_count, tickets, id FROM users ORDER BY referrals_count DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    # Map to expected keys used in API
    return [{'telegram_id': r.get('telegram_id'), 'referrals_count': r.get('referrals_count', 0), 'tickets': r.get('tickets', 0), 'id': r.get('id')} for r in rows]

# Ebooks
def get_all_ebooks():
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM ebooks')
    rows = cur.fetchall()
    conn.close()
    return rows

def purchase_ebook(user_id, ebook_id, amount_usd):
    # Simplified: add pool contribution to current active giveaway pool if exists
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM giveaway WHERE status = "active" ORDER BY id DESC LIMIT 1')
        g = cur.fetchone()
        # update pool if exists
        if g:
            new_pool = (g.get('pool_amount') or 0) + float(amount_usd) * 0.8
            cur.execute('UPDATE giveaway SET pool_amount = ? WHERE id = ?', (new_pool, g['id']))
        # increase user's tickets according to amount (1 ticket per $1 simplified)
        cur.execute('UPDATE users SET tickets = tickets + ? WHERE id = ?', (int(amount_usd), int(user_id)))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

# Giveaway helpers
def create_giveaway(pool_amount=15.0, duration_hours=24.0, num_winners=1):
    conn = _connect()
    cur = conn.cursor()
    created = datetime.utcnow().replace(microsecond=0)
    ends = created + timedelta(hours=float(duration_hours))
    ends_iso = ends.isoformat() + 'Z'
    cur.execute('INSERT INTO giveaway (pool_amount, num_winners, status, created_at, ends_at) VALUES (?, ?, ?, ?, ?)',
                (float(pool_amount), int(num_winners), 'active', created.isoformat() + 'Z', ends_iso))
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid

def get_giveaway_status():
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM giveaway WHERE status = "active" ORDER BY id DESC LIMIT 1')
    row = cur.fetchone()
    conn.close()
    return row

def join_giveaway(giveaway_id, user_id, tickets_spent):
    conn = _connect()
    cur = conn.cursor()
    try:
        # ensure user has enough tickets
        cur.execute('SELECT tickets FROM users WHERE id = ?', (int(user_id),))
        u = cur.fetchone()
        if not u or (u.get('tickets') or 0) < int(tickets_spent):
            conn.close()
            return False
        # deduct tickets
        cur.execute('UPDATE users SET tickets = tickets - ? WHERE id = ?', (int(tickets_spent), int(user_id)))
        # insert participant (or update tickets_spent sum)
        cur.execute('SELECT * FROM giveaway_participants WHERE giveaway_id = ? AND user_id = ?', (int(giveaway_id), int(user_id)))
        existing = cur.fetchone()
        if existing:
            cur.execute('UPDATE giveaway_participants SET tickets_spent = tickets_spent + ? WHERE id = ?', (int(tickets_spent), existing['id']))
        else:
            cur.execute('INSERT INTO giveaway_participants (giveaway_id, user_id, tickets_spent) VALUES (?, ?, ?)', (int(giveaway_id), int(user_id), int(tickets_spent)))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def draw_winner(giveaway_id):
    # wrapper to be consistent with giveaway.draw_winner
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT user_id, tickets_spent FROM giveaway_participants WHERE giveaway_id = ?', (int(giveaway_id),))
    parts = cur.fetchall()
    conn.close()
    if not parts:
        return None
    users = [p['user_id'] for p in parts]
    weights = [p['tickets_spent'] for p in parts]
    import random
    return random.choices(users, weights=weights, k=1)[0]

def create_payout_entry(giveaway_id, user_id):
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM giveaway_payouts WHERE giveaway_id = ? AND user_id = ?', (int(giveaway_id), int(user_id)))
        if not cur.fetchone():
            cur.execute('INSERT INTO giveaway_payouts (giveaway_id, user_id, currency, address, confirmed_at) VALUES (?, ?, ?, ?, ?)',
                        (int(giveaway_id), int(user_id), None, None, None))
            conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def get_payout(giveaway_id, user_id):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM giveaway_payouts WHERE giveaway_id = ? AND user_id = ?', (int(giveaway_id), int(user_id)))
    row = cur.fetchone()
    conn.close()
    return row

def confirm_payout(giveaway_id, user_id, currency, address):
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute('SELECT confirmed_at FROM giveaway_payouts WHERE giveaway_id = ? AND user_id = ?', (int(giveaway_id), int(user_id)))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False, 'No payout entry found'
        if row.get('confirmed_at'):
            conn.close()
            return False, 'Payout already confirmed'
        confirmed_at = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        cur.execute('UPDATE giveaway_payouts SET currency = ?, address = ?, confirmed_at = ? WHERE giveaway_id = ? AND user_id = ?',
                    (currency, address, confirmed_at, int(giveaway_id), int(user_id)))
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def get_unconfirmed_payout_for_user(user_id):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('''SELECT gp.*, g.id as giveaway_id, g.pool_amount, g.ended_at
                   FROM giveaway_payouts gp
                   JOIN giveaway g ON gp.giveaway_id = g.id
                   WHERE gp.user_id = ? AND gp.confirmed_at IS NULL AND g.status = 'ended'
                   ORDER BY g.ended_at DESC LIMIT 1''', (int(user_id),))
    row = cur.fetchone()
    conn.close()
    return row

def end_giveaway(giveaway_id, winner_id):
    conn = _connect()
    cur = conn.cursor()
    try:
        ended_at = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        cur.execute('UPDATE giveaway SET status = ?, winner_id = ?, ended_at = ? WHERE id = ?', ('ended', winner_id, ended_at, int(giveaway_id)))
        # create payout entry for winner so frontend can prompt them
        if winner_id:
            cur.execute('SELECT * FROM giveaway_payouts WHERE giveaway_id = ? AND user_id = ?', (int(giveaway_id), int(winner_id)))
            if not cur.fetchone():
                cur.execute('INSERT INTO giveaway_payouts (giveaway_id, user_id, currency, address, confirmed_at) VALUES (?, ?, ?, ?, ?)',
                            (int(giveaway_id), int(winner_id), None, None, None))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()
