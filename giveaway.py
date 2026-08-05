import random
import json
from datetime import datetime
from database import (
    get_db_connection, get_giveaway_status, end_giveaway,
    join_giveaway, get_user_by_id
)

class GiveawayManager:
    """Manages giveaway operations"""
    POOL_CONTRIBUTION_RATE = 0.8  # 80% of purchases go to pool
    
    @staticmethod
    def check_and_start_giveaway():
        """Automatic start disabled: giveaways must be created from admin panel."""
        # For now we don't auto-start giveaways based on pool. Admin must create giveaways.
        return False
    
    @staticmethod
    def calculate_remaining_time(ends_at_str):
        """Calculate remaining time in seconds until giveaway ends"""
        if not ends_at_str:
            return None
        
        try:
            # Parse ISO format datetime
            if isinstance(ends_at_str, str):
                ends_at = datetime.fromisoformat(ends_at_str.replace('Z', '+00:00'))
            else:
                ends_at = ends_at_str
            
            # Use a 'now' compatible with ends_at: if ends_at has tzinfo use same tz, else use naive UTC
            if getattr(ends_at, 'tzinfo', None):
                now = datetime.now(tz=ends_at.tzinfo)
            else:
                now = datetime.utcnow()
            
            remaining = (ends_at - now).total_seconds()
            
            return max(0, remaining)  # Return 0 if time has expired
        except Exception:
            return None
    
    @staticmethod
    def format_remaining_time(seconds):
        """Format remaining seconds as human readable string"""
        if seconds is None or seconds <= 0:
            return "Ended"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @staticmethod
    def get_current_giveaway():
        """Get current active giveaway info with remaining time"""
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
        
        # Calculate remaining time
        remaining_seconds = GiveawayManager.calculate_remaining_time(giveaway.get('ends_at'))
        remaining_formatted = GiveawayManager.format_remaining_time(remaining_seconds)
        
        return {
            'id': giveaway['id'],
            'pool_amount': giveaway['pool_amount'],
            'status': giveaway['status'],
            'participants': participant_count,
            'created_at': giveaway['created_at'],
            'ends_at': giveaway.get('ends_at'),
            'remaining_seconds': remaining_seconds,
            'remaining_time': remaining_formatted
        }
    
    @staticmethod
    def user_join_giveaway(user_id, tickets_to_spend):
        """User joins current giveaway. Users must spend ALL their tickets to join."""
        # Get current active giveaway
        giveaway = get_giveaway_status()
        
        if not giveaway:
            return False, "No active giveaway"
        
        # Validate user exists
        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Enforce spending maximum tickets only
        user_tickets = int(user.get('tickets', 0) or 0)
        if user_tickets <= 0:
            return False, "No tickets available"
        
        # If tickets_to_spend is None, treat as intent to spend all tickets
        if tickets_to_spend is None:
            tickets_to_spend = user_tickets
        
        # Only allow spending exactly all tickets (maximum)
        try:
            tickets_to_spend = int(tickets_to_spend)
        except (ValueError, TypeError):
            return False, "Invalid tickets_to_spend"
        
        if tickets_to_spend != user_tickets:
            return False, "You must spend all your tickets to join"
        
        # Manual mode: spend specified tickets (which must equal user's tickets now)
        if user_tickets < tickets_to_spend:
            return False, "Insufficient tickets"
        
        result = join_giveaway(giveaway['id'], user_id, tickets_to_spend)
        if isinstance(result, tuple):
            return result
        return (bool(result), "Successfully joined giveaway" if result else "Failed to join giveaway")
    
    @staticmethod
    def draw_winner(giveaway_id):
        """Draw random winner from participants"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all participants with their weights (tickets spent)
        cursor.execute(
            """SELECT user_id, tickets_spent FROM giveaway_participants 
               WHERE giveaway_id = ? ORDER BY user_id""",
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
            # No participants — still finalize giveaway (no winner)
            success = end_giveaway(giveaway_id, None)
            if success:
                return True, {
                    'winner_id': None,
                    'winner_telegram_id': None,
                    'message': 'Giveaway ended with no participants'
                }
            else:
                return False, "Failed to end giveaway"
        
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
            """SELECT * FROM giveaway WHERE status = "ended" 
               ORDER BY ended_at DESC LIMIT ?""",
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
