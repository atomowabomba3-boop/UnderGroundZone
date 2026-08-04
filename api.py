"""
UnderGroundZone - Main Flask API
Telegram Mini App Backend for Tickets & E-books Trading
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
from functools import wraps

from database import (
    init_db, get_user, create_user, update_user_tickets,
    get_all_ebooks, get_giveaway_pool, add_to_giveaway_pool,
    get_top_referrers, get_connection
)
from giveaway import start_giveaway, end_giveaway, join_giveaway
from utils import calculate_referral_bonus, validate_telegram_id

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()

# ============================================
# MIDDLEWARE & HELPERS
# ============================================

def require_telegram_id(f):
    """Decorator to validate telegram_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        telegram_id = request.headers.get('X-Telegram-ID') or request.json.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'error': 'Missing telegram_id'}), 400
        
        if not validate_telegram_id(telegram_id):
            return jsonify({'error': 'Invalid telegram_id format'}), 400
        
        return f(telegram_id, *args, **kwargs)
    return decorated_function

# ============================================
# USER ENDPOINTS
# ============================================

@app.route('/start', methods=['POST'])
def start():
    """Register new user with telegram_id"""
    data = request.json
    telegram_id = data.get('telegram_id')
    
    if not telegram_id or not validate_telegram_id(telegram_id):
        return jsonify({'error': 'Invalid telegram_id'}), 400
    
    # Check if user exists
    user = get_user(telegram_id)
    
    if user:
        return jsonify({
            'status': 'existing',
            'user': user
        }), 200
    
    # Create new user
    if create_user(telegram_id):
        new_user = get_user(telegram_id)
        return jsonify({
            'status': 'created',
            'user': new_user
        }), 201
    else:
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/me', methods=['GET'])
@require_telegram_id
def get_me(telegram_id):
    """Get current user data"""
    user = get_user(telegram_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user), 200

# ============================================
# REFERRAL ENDPOINTS
# ============================================

@app.route('/referral', methods=['POST'])
@require_telegram_id
def add_referral(telegram_id):
    """Add referral and calculate bonuses"""
    data = request.json
    referred_telegram_id = data.get('referred_telegram_id')
    
    if not referred_telegram_id:
        return jsonify({'error': 'Missing referred_telegram_id'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get referrer user
        referrer = get_user(telegram_id)
        if not referrer:
            return jsonify({'error': 'Referrer not found'}), 404
        
        # Get referred user or create
        referred = get_user(referred_telegram_id)
        if not referred:
            create_user(referred_telegram_id)
            referred = get_user(referred_telegram_id)
        
        referrer_id = referrer['id']
        referred_id = referred['id']
        
        # Check if referral already exists
        cursor.execute(
            'SELECT * FROM referrals WHERE referrer_id = ? AND referred_id = ?',
            (referrer_id, referred_id)
        )
        
        if cursor.fetchone():
            return jsonify({'error': 'Referral already exists'}), 409
        
        # Add referral record
        cursor.execute(
            'INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)',
            (referrer_id, referred_id)
        )
        
        # Update referral count
        new_referral_count = referrer['referrals'] + 1
        cursor.execute(
            'UPDATE users SET referrals = ? WHERE id = ?',
            (new_referral_count, referrer_id)
        )
        
        # Calculate bonus tickets
        bonus_tickets = calculate_referral_bonus(new_referral_count)
        if bonus_tickets > 0:
            new_tickets = referrer['tickets'] + bonus_tickets
            cursor.execute(
                'UPDATE users SET tickets = ? WHERE id = ?',
                (new_tickets, referrer_id)
            )
        
        conn.commit()
        
        updated_user = get_user(telegram_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Referral added. Bonus: {bonus_tickets} tickets',
            'user': updated_user
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================
# EBOOK ENDPOINTS
# ============================================

@app.route('/ebooks', methods=['GET'])
def get_ebooks():
    """Get all available ebooks"""
    ebooks = get_all_ebooks()
    return jsonify(ebooks), 200

@app.route('/buy-ebook', methods=['POST'])
@require_telegram_id
def buy_ebook(telegram_id):
    """Buy ebook with webhook from crypto bot"""
    data = request.json
    ebook_id = data.get('ebook_id')
    amount_usd = data.get('amount_usd')
    
    if not ebook_id or not amount_usd:
        return jsonify({'error': 'Missing ebook_id or amount_usd'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        user = get_user(telegram_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get ebook
        cursor.execute('SELECT * FROM ebooks WHERE id = ?', (ebook_id,))
        ebook = cursor.fetchone()
        if not ebook:
            return jsonify({'error': 'Ebook not found'}), 404
        
        # Record purchase
        cursor.execute(
            'INSERT INTO purchases (user_id, ebook_id, amount_usd) VALUES (?, ?, ?)',
            (user['id'], ebook_id, amount_usd)
        )
        
        # Add tickets to user
        new_tickets = user['tickets'] + ebook['tickets_reward']
        cursor.execute(
            'UPDATE users SET tickets = ? WHERE id = ?',
            (new_tickets, user['id'])
        )
        
        # Add ebook to owned list
        owned_ebooks = json.loads(user['ebooks_owned']) if user['ebooks_owned'] else []
        if ebook_id not in owned_ebooks:
            owned_ebooks.append(ebook_id)
            cursor.execute(
                'UPDATE users SET ebooks_owned = ? WHERE id = ?',
                (json.dumps(owned_ebooks), user['id'])
            )
        
        # Add 80% to giveaway pool
        add_to_giveaway_pool(amount_usd)
        
        conn.commit()
        updated_user = get_user(telegram_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Ebook purchased. +{ebook["tickets_reward"]} tickets',
            'user': updated_user
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================
# RANKING ENDPOINT
# ============================================

@app.route('/ranking', methods=['GET'])
def get_ranking():
    """Get top 10 referrers"""
    top_users = get_top_referrers(10)
    
    ranking = [
        {
            'rank': i + 1,
            'telegram_id': user['telegram_id'],
            'referrals': user['referrals'],
            'tickets': user['tickets']
        }
        for i, user in enumerate(top_users)
    ]
    
    return jsonify(ranking), 200

# ============================================
# GIVEAWAY ENDPOINTS
# ============================================

@app.route('/giveaway/status', methods=['GET'])
def giveaway_status():
    """Get current giveaway status and pool"""
    pool = get_giveaway_pool()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM giveaway WHERE status = ? ORDER BY id DESC LIMIT 1', ('active',))
    giveaway = cursor.fetchone()
    conn.close()
    
    if giveaway:
        cursor.execute(
            'SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = ?',
            (giveaway['id'],)
        )
        participants_count = cursor.fetchone()['count']
        
        return jsonify({
            'pool_usd': giveaway['pool_usd'],
            'status': giveaway['status'],
            'participants': participants_count,
            'ghost_threshold_reached': giveaway['pool_usd'] >= 15
        }), 200
    else:
        return jsonify({'pool_usd': 0, 'status': 'inactive'}), 200

@app.route('/giveaway/start', methods=['POST'])
def start_giveaway_endpoint():
    """Start new giveaway"""
    result = start_giveaway()
    if result:
        return jsonify({'status': 'success', 'message': 'Giveaway started'}), 201
    else:
        return jsonify({'error': 'Failed to start giveaway'}), 500

@app.route('/giveaway/join', methods=['POST'])
@require_telegram_id
def join_giveaway_endpoint(telegram_id):
    """Join giveaway with tickets"""
    data = request.json
    tickets_spent = data.get('tickets_spent')
    
    if not tickets_spent or tickets_spent <= 0:
        return jsonify({'error': 'Invalid tickets amount'}), 400
    
    result = join_giveaway(telegram_id, tickets_spent)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({'error': result.get('error', 'Failed to join giveaway')}), 400

@app.route('/giveaway/end', methods=['POST'])
def end_giveaway_endpoint():
    """End giveaway and pick winner"""
    result = end_giveaway()
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({'error': result.get('error', 'Failed to end giveaway')}), 500

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', False)
    app.run(host='0.0.0.0', port=port, debug=debug)
