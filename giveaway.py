"""
Giveaway module for UnderGroundZone
Handles giveaway logic, pool management, and winner selection
"""

import random
import json
from datetime import datetime
from database import get_connection, get_user, update_user_tickets

def start_giveaway():
    """Start a new giveaway"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if there's already an active giveaway
        cursor.execute('SELECT * FROM giveaway WHERE status = ?', ('active',))
        if cursor.fetchone():
            return False
        
        # Create new giveaway
        cursor.execute(
            'INSERT INTO giveaway (pool_usd, status) VALUES (?, ?)',
            (0, 'active')
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error starting giveaway: {e}")
        return False
    finally:
        conn.close()

def join_giveaway(telegram_id, tickets_spent):
    """Join active giveaway with tickets"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        user = get_user(telegram_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Check if user has enough tickets
        if user['tickets'] < tickets_spent:
            return {'success': False, 'error': 'Not enough tickets'}
        
        # Get active giveaway
        cursor.execute('SELECT * FROM giveaway WHERE status = ?', ('active',))
        giveaway = cursor.fetchone()
        
        if not giveaway:
            return {'success': False, 'error': 'No active giveaway'}
        
        # Check if giveaway pool reached ghost threshold ($15)
        if giveaway['pool_usd'] < 15:
            return {'success': False, 'error': 'Giveaway pool has not reached minimum threshold ($15)'}
        
        # Add participant
        cursor.execute(
            'INSERT INTO giveaway_participants (giveaway_id, user_id, tickets_spent) VALUES (?, ?, ?)',
            (giveaway['id'], user['id'], tickets_spent)
        )
        
        # Deduct tickets from user
        new_tickets = user['tickets'] - tickets_spent
        cursor.execute(
            'UPDATE users SET tickets = ? WHERE id = ?',
            (new_tickets, user['id'])
        )
        
        conn.commit()
        
        return {
            'success': True,
            'message': f'Joined giveaway with {tickets_spent} tickets',
            'remaining_tickets': new_tickets
        }
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def end_giveaway():
    """End giveaway and select winner"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get active giveaway
        cursor.execute('SELECT * FROM giveaway WHERE status = ?', ('active',))
        giveaway = cursor.fetchone()
        
        if not giveaway:
            return {'success': False, 'error': 'No active giveaway'}
        
        # Get all participants
        cursor.execute(
            'SELECT * FROM giveaway_participants WHERE giveaway_id = ?',
            (giveaway['id'],)
        )
        participants = cursor.fetchall()
        
        if not participants:
            return {'success': False, 'error': 'No participants in giveaway'}
        
        # Select winner (weighted by tickets spent)
        participant_ids = []
        for participant in participants:
            # Add participant ID multiple times based on tickets spent
            participant_ids.extend([participant['user_id']] * participant['tickets_spent'])
        
        winner_user_id = random.choice(participant_ids)
        
        # Update giveaway with winner and end it
        cursor.execute(
            'UPDATE giveaway SET status = ?, winner_id = ?, ended_at = ? WHERE id = ?',
            ('ended', winner_user_id, datetime.now(), giveaway['id'])
        )
        
        # Reset all participants' tickets to 1
        cursor.execute(
            'SELECT DISTINCT user_id FROM giveaway_participants WHERE giveaway_id = ?',
            (giveaway['id'],)
        )
        participant_users = cursor.fetchall()
        
        for participant_user in participant_users:
            cursor.execute(
                'UPDATE users SET tickets = ? WHERE id = ?',
                (1, participant_user['user_id'])
            )
        
        # Give prize pool to winner (convert USD to tickets: $1 = 50 tickets)
        prize_tickets = int(giveaway['pool_usd'] * 50)
        cursor.execute(
            'UPDATE users SET tickets = tickets + ? WHERE id = ?',
            (prize_tickets, winner_user_id)
        )
        
        conn.commit()
        
        # Get winner info
        winner = get_user_by_id(winner_user_id)
        
        return {
            'success': True,
            'message': 'Giveaway ended',
            'winner_telegram_id': winner['telegram_id'] if winner else 'Unknown',
            'prize_usd': giveaway['pool_usd'],
            'prize_tickets': prize_tickets
        }
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Get user by database ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_giveaway_stats():
    """Get giveaway statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get active giveaway
    cursor.execute('SELECT * FROM giveaway WHERE status = ? ORDER BY id DESC LIMIT 1', ('active',))
    active_giveaway = cursor.fetchone()
    
    # Get last ended giveaway
    cursor.execute('SELECT * FROM giveaway WHERE status = ? ORDER BY ended_at DESC LIMIT 1', ('ended',))
    last_ended = cursor.fetchone()
    
    conn.close()
    
    stats = {
        'active': None,
        'last_ended': None
    }
    
    if active_giveaway:
        cursor.execute(
            'SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = ?',
            (active_giveaway['id'],)
        )
        participants_count = cursor.fetchone()['count']
        
        stats['active'] = {
            'pool_usd': active_giveaway['pool_usd'],
            'participants': participants_count,
            'ghost_threshold_reached': active_giveaway['pool_usd'] >= 15
        }
    
    if last_ended:
        winner = get_user_by_id(last_ended['winner_id'])
        stats['last_ended'] = {
            'pool_usd': last_ended['pool_usd'],
            'winner_telegram_id': winner['telegram_id'] if winner else 'Unknown',
            'ended_at': last_ended['ended_at']
        }
    
    return stats
