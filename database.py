import sqlite3
import json
from datetime import datetime, timedelta
import secrets

class Database:
    def __init__(self, path='database.db'):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite_row
        self._ensure_tables()

    def _ensure_tables(self):
        cur = self.conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            tickets INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            ebooks_owned TEXT DEFAULT '[]',
            referred_by TEXT DEFAULT NULL,
            created_at TEXT
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS giveaway_state (
            id INTEGER PRIMARY KEY,
            pool_cents INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            participants TEXT DEFAULT '[]',
            started_at TEXT,
            duration_minutes INTEGER
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            telegram_id TEXT,
            created_at TEXT,
            expires_at TEXT
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_token TEXT PRIMARY KEY,
            telegram_id TEXT,
            ebook_id INTEGER,
            amount_cents INTEGER,
            mode TEXT,
            status TEXT,
            created_at TEXT
        )
        ''')

        self.conn.commit()
        # ensure single row for giveaway
        cur.execute('SELECT COUNT(*) as c FROM giveaway_state')
        if cur.fetchone()['c'] == 0:
            cur.execute('INSERT INTO giveaway_state (pool_cents, is_active, participants) VALUES (0,0,?);', (json.dumps([]),))
            self.conn.commit()

    # user helpers
    def get_user(self, telegram_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
        row = cur.fetchone()
        if not row:
            return None
        user = dict(row)
        user['ebooks_owned'] = json.loads(user.get('ebooks_owned') or '[]')
        return user

    def create_user(self, telegram_id):
        cur = self.conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute('INSERT OR IGNORE INTO users (telegram_id, tickets, referrals, ebooks_owned, created_at) VALUES (?,?,?,?,?)', (str(telegram_id), 1, 0, json.dumps([]), now))
        self.conn.commit()

    def add_referral(self, referrer_id, referee_id):
        # create referee if not exists
        referee = self.get_user(referee_id)
        if referee and referee.get('referred_by'):
            return False, 'referee already linked'
        if not referee:
            self.create_user(referee_id)
        cur = self.conn.cursor()
        # set referred_by on referee
        cur.execute('UPDATE users SET referred_by = ? WHERE telegram_id = ?', (str(referrer_id), str(referee_id)))
        # increment referrer referrals
        cur.execute('UPDATE users SET referrals = referrals + 1, tickets = tickets + 1 WHERE telegram_id = ?', (str(referrer_id),))
        self.conn.commit()
        # apply progressive bonuses
        ref = self.get_user(referrer_id)
        if ref:
            total = ref.get('referrals', 0)
            bonus = referral_bonus_for_thresholds(total)
            if bonus > 0:
                cur.execute('UPDATE users SET tickets = tickets + ? WHERE telegram_id = ?', (bonus, str(referrer_id)))
                self.conn.commit()
                return True, f'referral added, bonus {bonus} tickets applied (total refs: {total})'
        return True, 'referral added'

    def get_ranking(self, limit=10):
        cur = self.conn.cursor()
        cur.execute('SELECT telegram_id, referrals, tickets FROM users ORDER BY referrals DESC, tickets DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def add_ebook_to_user(self, telegram_id, ebook_id, tickets_awarded=0):
        user = self.get_user(telegram_id)
        if not user:
            self.create_user(telegram_id)
            user = self.get_user(telegram_id)
        ebooks = user.get('ebooks_owned', [])
        if ebook_id in ebooks:
            return False
        ebooks.append(ebook_id)
        cur = self.conn.cursor()
        cur.execute('UPDATE users SET ebooks_owned = ?, tickets = tickets + ? WHERE telegram_id = ?', (json.dumps(ebooks), tickets_awarded, str(telegram_id)))
        self.conn.commit()
        return True

    def reset_tickets_for_participants(self, participants):
        cur = self.conn.cursor()
        for t in participants:
            cur.execute('UPDATE users SET tickets = 1 WHERE telegram_id = ?', (str(t),))
        self.conn.commit()

    def deduct_tickets(self, telegram_id, amount):
        cur = self.conn.cursor()
        cur.execute('SELECT tickets FROM users WHERE telegram_id = ?', (str(telegram_id),))
        row = cur.fetchone()
        if not row:
            return False
        if row['tickets'] < amount:
            return False
        cur.execute('UPDATE users SET tickets = tickets - ? WHERE telegram_id = ?', (amount, str(telegram_id)))
        self.conn.commit()
        return True

    # session helpers
    def create_session_token(self, telegram_id, days_valid=7):
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires = now + timedelta(days=days_valid)
        cur = self.conn.cursor()
        cur.execute('INSERT INTO sessions (token, telegram_id, created_at, expires_at) VALUES (?,?,?,?)', (token, str(telegram_id), now.isoformat(), expires.isoformat()))
        self.conn.commit()
        return token

    def get_telegram_by_token(self, token):
        cur = self.conn.cursor()
        cur.execute('SELECT telegram_id, expires_at FROM sessions WHERE token = ?', (token,))
        row = cur.fetchone()
        if not row:
            return None
        # check expiry
        try:
            expires = datetime.fromisoformat(row['expires_at'])
            if datetime.utcnow() > expires:
                # expired, delete
                cur.execute('DELETE FROM sessions WHERE token = ?', (token,))
                self.conn.commit()
                return None
        except Exception:
            pass
        return row['telegram_id']

    def get_all_users(self):
        cur = self.conn.cursor()
        cur.execute('SELECT telegram_id, tickets, referrals, ebooks_owned, referred_by, created_at FROM users ORDER BY referrals DESC')
        rows = cur.fetchall()
        results = []
        for r in rows:
            item = dict(r)
            item['ebooks_owned'] = json.loads(item.get('ebooks_owned') or '[]')
            results.append(item)
        return results

    # orders
    def create_order(self, telegram_id, ebook_id, amount_cents, mode='simulate'):
        order_token = secrets.token_urlsafe(16)
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute('INSERT INTO orders (order_token, telegram_id, ebook_id, amount_cents, mode, status, created_at) VALUES (?,?,?,?,?,?,?)', (order_token, str(telegram_id), int(ebook_id), int(amount_cents), mode, 'pending', now))
        self.conn.commit()
        return order_token

    def get_order(self, order_token):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM orders WHERE order_token = ?', (order_token,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)

    def mark_order_paid(self, order_token):
        cur = self.conn.cursor()
        cur.execute('UPDATE orders SET status = ? WHERE order_token = ?', ('paid', order_token))
        self.conn.commit()

    def list_orders(self):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 200')
        rows = cur.fetchall()
        return [dict(r) for r in rows]

# sqlite helpers

def sqlite_row(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# For referral bonus lookup without circular import
from utils import referral_bonus_for_thresholds
