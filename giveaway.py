import random
import json
from database import (
    get_db_connection, get_giveaway_status, end_giveaway,
    join_giveaway, get_user_by_id
)

class GiveawayManager:
    """Manages giveaway operations"""
    
    GHOST_THRESHOLD = 15.0  # $15 minimum to start giveaway
    POOL_CONTRIBUTION_RATE = 0.8  # 80% of purchases go to pool
    
    @staticmethod
    def check_and_start_giveaway():
        """Check if giveaway pool reached threshold and start if needed"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if there's an active giveaway
        cursor.execute('SELECT * FROM giveaway WHERE status = "active"')
        active = cursor.fetchone()
        
        if active:
            conn.close()
            return False
        
        # Check pool amount
        cursor.execute('SELECT pool_amount FROM giveaway ORDER BY created_at DESC LIMIT 1')
        last_giveaway = cursor.fetchone()
        
        if last_giveaway and last_giveaway['pool_amount'] >= GiveawayManager.GHOST_THRESHOLD:
            # Create new active giveaway
            cursor.execute(
                'INSERT INTO giveaway (status, pool_amount) VALUES (?, ?)',
                ('active', last_giveaway['pool_amount'])
            )
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    @staticmethod
    def get_current_giveaway():
        """Get current active giveaway info"""
        giveaway = get_giveaway_status()
        
        if not giveaway:
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count participants
        cursor.execute(
            'SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = ?',
            (giveaway['id'],)
        )
        participant_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'id': giveaway['id'],
            'pool_amount': giveaway['pool_amount'],
            'status': giveaway['status'],
            'participants': participant_count,
            'created_at': giveaway['created_at']
        }
    
    @staticmethod
    def user_join_giveaway(user_id, tickets_to_spend):
        """User joins current giveaway"""
        # Get current active giveaway
        giveaway = get_giveaway_status()
        
        if not giveaway:
            return False, "No active giveaway"
        
        # Validate user has enough tickets
        user = get_user_by_id(user_id)
        if not user or user['tickets'] < tickets_to_spend:
            return False, "Insufficient tickets"
        
        # Add to giveaway
        success = join_giveaway(giveaway['id'], user_id, tickets_to_spend)
        
        if success:
            return True, "Successfully joined giveaway"
        else:
            return False, "Failed to join giveaway"
    
    @staticmethod
    def draw_winner(giveaway_id):
        """Draw random winner from participants"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all participants with their weights (tickets spent)
        cursor.execute(
            '''SELECT user_id, tickets_spent FROM giveaway_participants 
               WHERE giveaway_id = ? ORDER BY user_id''',
            (giveaway_id,)
        )
        participants = cursor.fetchall()
        conn.close()
        
        if not participants:
            return None
        
        # Create weighted random selection
        users = [p['user_id'] for p in participants]
        weights = [p['tickets_spent'] for p in participants]
        
        winner_id = random.choices(users, weights=weights, k=1)[0]
        return winner_id
    
    @staticmethod
    def end_giveaway_round(giveaway_id):
        """End current giveaway round and draw winner"""
        # Draw winner
        winner_id = GiveawayManager.draw_winner(giveaway_id)
        
        if not winner_id:
            return False, "No participants to draw winner"
        
        # End giveaway (resets all participants' tickets to 1)
        success = end_giveaway(giveaway_id, winner_id)
        
        if success:
            winner = get_user_by_id(winner_id)
            return True, {
                'winner_id': winner_id,
                'winner_telegram_id': winner['telegram_id'] if winner else None,
                'message': f"Giveaway ended! Winner: User {winner_id}"
            }
        else:
            return False, "Failed to end giveaway"
    
    @staticmethod
    def get_giveaway_history(limit=10):
        """Get past giveaway rounds"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT * FROM giveaway WHERE status = "ended" 
               ORDER BY ended_at DESC LIMIT ?''',
            (limit,)
        )
        giveaways = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return giveaways
    
    @staticmethod
    def add_ebook_to_owner(user_id, ebook_id):
        """Add ebook to user's owned ebooks (robust handling of stored format)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ebooks_owned FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return False
        
        # ebooks_owned in DB may be stored as a JSON string or already as a Python list
        ebooks_field = user['ebooks_owned']
        try:
            if isinstance(ebooks_field, str):
                ebooks_owned = json.loads(ebooks_field)
            elif isinstance(ebooks_field, (list, tuple)):
                ebooks_owned = list(ebooks_field)
            else:
                # fallback
                ebooks_owned = []
        except Exception:
            ebooks_owned = []
        
        if ebook_id not in ebooks_owned:
            ebooks_owned.append(ebook_id)
            cursor.execute(
                'UPDATE users SET ebooks_owned = ? WHERE id = ?',
                (json.dumps(ebooks_owned), user_id)
            )
            conn.commit()
        
        conn.close()
        return True
