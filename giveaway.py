import json
import os
from datetime import datetime, timedelta
import secrets

class GiveawayManager:
    def __init__(self, db):
        self.db = db

    def _state(self):
        cur = self.db.conn.cursor()
        cur.execute('SELECT * FROM giveaway_state WHERE id = 1')
        row = cur.fetchone()
        if not row:
            return None
        state = dict(row)
        state['participants'] = json.loads(state.get('participants') or '[]')
        return state

    def get_state(self):
        s = self._state()
        if not s:
            return {'pool_cents': 0, 'is_active': False, 'participants': []}
        return {'pool_cents': s['pool_cents'], 'is_active': bool(s['is_active']), 'participants': s['participants']}

    def add_to_pool(self, cents):
        cur = self.db.conn.cursor()
        cur.execute('UPDATE giveaway_state SET pool_cents = pool_cents + ? WHERE id = 1', (int(cents),))
        self.db.conn.commit()

    def start(self, duration_minutes=None):
        cur = self.db.conn.cursor()
        cur.execute('UPDATE giveaway_state SET is_active = 1, started_at = ?, duration_minutes = ? WHERE id = 1', (datetime.utcnow().isoformat(), duration_minutes))
        self.db.conn.commit()

    def join(self, telegram_id, cost=1):
        state = self._state()
        if not state or state['is_active'] != 1:
            return False, 'giveaway not active'
        # check user has enough tickets
        user = self.db.get_user(telegram_id)
        if not user:
            return False, 'user not found'
        if user['tickets'] < cost:
            return False, 'not enough tickets'
        # deduct tickets
        ok = self.db.deduct_tickets(telegram_id, cost)
        if not ok:
            return False, 'failed to deduct tickets'
        parts = state['participants']
        if telegram_id in parts:
            return False, 'already joined'
        parts.append(telegram_id)
        cur = self.db.conn.cursor()
        cur.execute('UPDATE giveaway_state SET participants = ? WHERE id = 1', (json.dumps(parts),))
        self.db.conn.commit()
        return True, 'joined giveaway'

    def end(self):
        state = self._state()
        if not state or state['is_active'] != 1:
            return {'error': 'no active giveaway'}
        if not state['participants']:
            # reset state
            cur = self.db.conn.cursor()
            cur.execute('UPDATE giveaway_state SET is_active = 0, participants = ?, pool_cents = 0 WHERE id = 1', (json.dumps([]),))
            self.db.conn.commit()
            return {'ok': True, 'message': 'no participants, pool cleared'}
        # choose winner
        winner = secrets.choice(state['participants'])
        pool = state['pool_cents']
        # reset participants' tickets to 1
        self.db.reset_tickets_for_participants(state['participants'])
        # reset pool and participants and deactivate
        cur = self.db.conn.cursor()
        cur.execute('UPDATE giveaway_state SET is_active = 0, participants = ?, pool_cents = 0 WHERE id = 1', (json.dumps([]),))
        self.db.conn.commit()
        return {'ok': True, 'winner': winner, 'pool_cents': pool}
