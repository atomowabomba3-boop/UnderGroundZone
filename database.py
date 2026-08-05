import sqlite3
import os
from datetime import datetime

# Use a writable default path inside the container (Railway) to avoid permission errors
DB_PATH = os.getenv('DB_PATH', '/tmp/underground_zone.db')

# Ensure directory exists for DB_PATH (handles cases where a custom path is provided)
_db_dir = os.path.dirname(DB_PATH)
if _db_dir and not os.path.exists(_db_dir):
    try:
        os.makedirs(_db_dir, exist_ok=True)
    except Exception:
        # Best-effort: if we cannot create the dir, we'll rely on SQLite to raise an informative error
        pass

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            tickets INTEGER DEFAULT 1,
            referrals_count INTEGER DEFAULT 0,
            ebooks_owned TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Referrals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users(id),
            FOREIGN KEY (referred_id) REFERENCES users(id)
        )
    ''')
    
    # Ebooks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ebooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            tickets_reward INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            cover_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed sample ebooks if table empty
    try:
        cursor.execute('SELECT COUNT(*) as c FROM ebooks')
        count_row = cursor.fetchone()
        count = count_row['c'] if count_row else 0
        if count == 0:
            # Using placeholder cover_image URLs; file_path references raw files in repo/ebooks (if available) or names
            cursor.execute('INSERT INTO ebooks (name, price, tickets_reward, file_path, cover_image) VALUES (?, ?, ?, ?, ?)',
                           ('Learn JS', 2.0, 50, 'learn_js.pdf', 'https://via.placeholder.com/300x420.png?text=Learn+JS'))
            cursor.execute('INSERT INTO ebooks (name, price, tickets_reward, file_path, cover_image) VALUES (?, ?, ?, ?, ?)',
                           ('Python Basics', 5.0, 150, 'python_basics.pdf', 'https://via.placeholder.com/300x420.png?text=Python+Basics'))
            cursor.execute('INSERT INTO ebooks (name, price, tickets_reward, file_path, cover_image) VALUES (?, ?, ?, ?, ?)',
                           ('Advanced Security', 10.0, 500, 'advanced_security.pdf', 'https://via.placeholder.com/300x420.png?text=Advanced+Security'))
    except Exception:
        # If seeding fails, continue without crashing
        pass
    
    # Giveaway table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giveaway (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_amount REAL DEFAULT 0.0,
            status TEXT DEFAULT 'inactive',
            winner_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (winner_id) REFERENCES users(id)
        )
    ''')
    
    # Giveaway participants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giveaway_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giveaway_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            tickets_spent INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (giveaway_id) REFERENCES giveaway(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Ensure unique index to avoid duplicate participants (protects against race conditions)
    try:
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_giveaway_participant ON giveaway_participants(giveaway_id, user_id)')
    except Exception:
        pass
    
    # Purchases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ebook_id INTEGER NOT NULL,
            amount_usd REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (ebook_id) REFERENCES ebooks(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(telegram_id):
    """Create new user with initial ticket"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (telegram_id, tickets) VALUES (?, ?)',
            (telegram_id, 1)
        )
        conn.commit()
        user_id = cursor.lastrowid
        # Return a user dict consistent with format_user_response expectations
        return {'id': user_id, 'telegram_id': telegram_id, 'tickets': 1, 'referrals_count': 0, 'ebooks_owned': '[]'}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user(telegram_id):
    """Get user by telegram_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    """Get user by user ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_tickets(user_id, tickets_change):
    """Update user tickets"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET tickets = tickets + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (tickets_change, user_id)
    )
    conn.commit()
    conn.close()

def add_referral(referrer_telegram_id, referred_telegram_id):
    """Add referral and reward referrer (prevents duplicates and applies bonuses)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user IDs
    cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (referrer_telegram_id,))
    referrer = cursor.fetchone()
    cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (referred_telegram_id,))
    referred = cursor.fetchone()

    if not referrer or not referred:
        conn.close()
        return False

    referrer_id = referrer['id']
    referred_id = referred['id']

    try:
        # Prevent duplicate referrals
        cursor.execute('SELECT 1 FROM referrals WHERE referrer_id = ? AND referred_id = ?', (referrer_id, referred_id))
        if cursor.fetchone():
            conn.close()
            return False  # already referred

        # Insert referral record
        cursor.execute('INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)', (referrer_id, referred_id))

        # Atomically increment referrals_count and give immediate +1 ticket reward
        cursor.execute('UPDATE users SET referrals_count = referrals_count + 1, tickets = tickets + 1 WHERE id = ?', (referrer_id,))

        # Read updated referrals_count to apply milestone bonuses
        cursor.execute('SELECT referrals_count FROM users WHERE id = ?', (referrer_id,))
        ref_count = cursor.fetchone()['referrals_count']

        bonus = 0
        if ref_count == 5:
            bonus = 5
        elif ref_count == 10:
            bonus = 15
        elif ref_count == 25:
            bonus = 40
        elif ref_count == 50:
            bonus = 100
        elif ref_count == 100:
            bonus = 300

        if bonus > 0:
            cursor.execute('UPDATE users SET tickets = tickets + ? WHERE id = ?', (bonus, referrer_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def get_ranking():
    """Get top 10 users by referrals"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT telegram_id, referrals_count, tickets FROM users ORDER BY referrals_count DESC LIMIT 10'
    )
    ranking = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ranking

def add_ebook(name, price, file_path, cover_image=None):
    """Add new ebook to database"""
    tickets_reward = {2: 50, 5: 150, 10: 500}.get(price, 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO ebooks (name, price, tickets_reward, file_path, cover_image) VALUES (?, ?, ?, ?, ?)',
            (name, price, tickets_reward, file_path, cover_image)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_ebooks():
    """Get all ebooks"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ebooks')
    ebooks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ebooks

def purchase_ebook(user_id, ebook_id, amount_usd):
    """Record ebook purchase and update user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get ebook details
    cursor.execute('SELECT tickets_reward FROM ebooks WHERE id = ?', (ebook_id,))
    ebook = cursor.fetchone()
    
    if not ebook:
        conn.close()
        return False
    
    try:
        # Record purchase
        cursor.execute(
            'INSERT INTO purchases (user_id, ebook_id, amount_usd) VALUES (?, ?, ?)',
            (user_id, ebook_id, amount_usd)
        )
        
        # Add tickets to user
        cursor.execute(
            'UPDATE users SET tickets = tickets + ? WHERE id = ?',
            (ebook['tickets_reward'], user_id)
        )
        
        # Add to giveaway pool (80% of purchase)
        giveaway_contribution = amount_usd * 0.8
        cursor.execute(
            'UPDATE giveaway SET pool_amount = pool_amount + ? WHERE status = "active"',
            (giveaway_contribution,)
        )
        
        conn.commit()
        return True
    except Exception:
        conn.close()
        return False
    finally:
        conn.close()

def get_giveaway_status():
    """Get current giveaway status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM giveaway WHERE status = "active" ORDER BY created_at DESC LIMIT 1'
    )
    giveaway = cursor.fetchone()
    conn.close()
    return dict(giveaway) if giveaway else None

def create_giveaway():
    """Create new giveaway"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO giveaway (status, pool_amount) VALUES (?, ?)',
        ('active', 0.0)
    )
    conn.commit()
    giveaway_id = cursor.lastrowid
    conn.close()
    return giveaway_id

def join_giveaway(giveaway_id, user_id, tickets_spent):
    """User joins giveaway (manual tickets) — returns (success, message)
    Now: supports adding tickets to an existing participant record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Basic validation
        if tickets_spent is None or tickets_spent < 1:
            return False, 'Tickets must be >= 1'

        # Get current user tickets
        cursor.execute('SELECT tickets FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, 'User not found'
        current_tickets = row['tickets'] or 0

        if current_tickets < tickets_spent:
            return False, 'Insufficient tickets'

        # Start transaction
        # Check if participant exists
        cursor.execute(
            'SELECT id FROM giveaway_participants WHERE giveaway_id = ? AND user_id = ?',
            (giveaway_id, user_id)
        )
        participant = cursor.fetchone()

        if participant:
            # Increment existing participant's tickets_spent
            cursor.execute(
                'UPDATE giveaway_participants SET tickets_spent = tickets_spent + ? WHERE id = ?',
                (tickets_spent, participant['id'])
            )
        else:
            # Insert new participation record
            cursor.execute(
                'INSERT INTO giveaway_participants (giveaway_id, user_id, tickets_spent) VALUES (?, ?, ?)',
                (giveaway_id, user_id, tickets_spent)
            )

        # Deduct tickets from user
        cursor.execute(
            'UPDATE users SET tickets = tickets - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (tickets_spent, user_id)
        )

        conn.commit()
        return True, 'Successfully joined giveaway'
    except sqlite3.IntegrityError:
        conn.rollback()
        return False, 'You are already in the giveaway'
    except Exception:
        conn.rollback()
        return False, 'Failed to join giveaway'
    finally:
        conn.close()


def join_giveaway_auto(giveaway_id, user_id):
    """User joins giveaway spending all their tickets except 1 (leaves user with 1 ticket).
    Supports adding to existing participant's tickets_spent instead of rejecting.
    Returns (success: bool, message: str).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if giveaway_id is None:
            return False, "No active giveaway"

        # Get current tickets
        cursor.execute('SELECT tickets FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, 'User not found'

        current_tickets = row['tickets'] or 0
        tickets_to_spend = max(current_tickets - 1, 0)

        if tickets_to_spend < 1:
            return False, 'Insufficient tickets to join (need at least 2 to auto-spend)'

        # Check if participant exists
        cursor.execute(
            'SELECT id FROM giveaway_participants WHERE giveaway_id = ? AND user_id = ?',
            (giveaway_id, user_id)
        )
        participant = cursor.fetchone()

        if participant:
            # Add to existing participant tickets_spent
            cursor.execute(
                'UPDATE giveaway_participants SET tickets_spent = tickets_spent + ? WHERE id = ?',
                (tickets_to_spend, participant['id'])
            )
        else:
            # Insert participant record
            cursor.execute(
                'INSERT INTO giveaway_participants (giveaway_id, user_id, tickets_spent) VALUES (?, ?, ?)',
                (giveaway_id, user_id, tickets_to_spend)
            )

        # Set user's tickets to 1 (preserve 1)
        cursor.execute(
            'UPDATE users SET tickets = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )

        conn.commit()
        return True, f"Successfully joined giveaway using {tickets_to_spend} tickets (1 ticket preserved)."
    except sqlite3.IntegrityError:
        conn.rollback()
        return False, 'You are already in the giveaway'
    except Exception:
        conn.rollback()
        return False, 'Failed to join giveaway'
    finally:
        conn.close()

def end_giveaway(giveaway_id, winner_id):
    """End giveaway and reset users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update giveaway status
        cursor.execute(
            'UPDATE giveaway SET status = ?, winner_id = ?, ended_at = CURRENT_TIMESTAMP WHERE id = ?',
            ('ended', winner_id, giveaway_id)
        )
        
        # Get all participants in this giveaway
        cursor.execute(
            'SELECT DISTINCT user_id FROM giveaway_participants WHERE giveaway_id = ?',
            (giveaway_id,)
        )
        participants = cursor.fetchall()
        
        # Reset their tickets to 1
        for participant in participants:
            cursor.execute(
                'UPDATE users SET tickets = 1 WHERE id = ?',
                (participant['user_id'],)
            )
        
        # Reset giveaway pool
        cursor.execute(
            'UPDATE giveaway SET pool_amount = 0 WHERE id = ?',
            (giveaway_id,)
        )
        
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()
