from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

from database import (
    init_db, create_user, get_user, get_user_by_id, update_user_tickets,
    add_referral, get_ranking, get_all_ebooks, purchase_ebook
)
from giveaway import GiveawayManager
from utils import (
    require_telegram_id, require_crypto_webhook, format_user_response,
    format_ebook_response
)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize database on startup
with app.app_context():
    init_db()

# ==================== USER ENDPOINTS ====================

@app.route('/start', methods=['POST'])
def start():
    """Register new user or return existing user"""
    data = request.json or {}
    telegram_id = data.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'error': 'Missing telegram_id'}), 400
    
    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid telegram_id'}), 400
    
    # Check if user exists
    user = get_user(telegram_id)
    
    if not user:
        # Create new user
        user = create_user(telegram_id)
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
    
    return jsonify({
        'status': 'success',
        'user': format_user_response(user)
    }), 200

@app.route('/me', methods=['GET'])
@require_telegram_id
def get_me(telegram_id):
    """Get current user data"""
    user = get_user(telegram_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'status': 'success',
        'user': format_user_response(user)
    }), 200

# ==================== REFERRAL ENDPOINTS ====================

@app.route('/referral', methods=['POST'])
def add_referral_endpoint():
    """Add referral link"""
    data = request.json or {}
    referrer_telegram_id = data.get('referrer_telegram_id')
    referred_telegram_id = data.get('referred_telegram_id')
    
    if not referrer_telegram_id or not referred_telegram_id:
        return jsonify({'error': 'Missing telegram_ids'}), 400
    
    try:
        referrer_telegram_id = int(referrer_telegram_id)
        referred_telegram_id = int(referred_telegram_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid telegram_ids'}), 400
    
    success = add_referral(referrer_telegram_id, referred_telegram_id)
    
    if success:
        referrer = get_user(referrer_telegram_id)
        return jsonify({
            'status': 'success',
            'message': 'Referral added',
            'referrer': format_user_response(referrer)
        }), 200
    else:
        return jsonify({'error': 'Failed to add referral'}), 400

@app.route('/ranking', methods=['GET'])
def get_ranking_endpoint():
    """Get top 10 users by referrals"""
    ranking = get_ranking()
    
    formatted_ranking = []
    for idx, user in enumerate(ranking, 1):
        formatted_ranking.append({
            'position': idx,
            'telegram_id': user['telegram_id'],
            'referrals': user['referrals_count'],
            'tickets': user['tickets']
        })
    
    return jsonify({
        'status': 'success',
        'ranking': formatted_ranking
    }), 200

# ==================== EBOOK ENDPOINTS ====================

@app.route('/ebooks', methods=['GET'])
def get_ebooks():
    """Get all available ebooks"""
    ebooks = get_all_ebooks()
    
    formatted_ebooks = [format_ebook_response(ebook) for ebook in ebooks]
    
    return jsonify({
        'status': 'success',
        'ebooks': formatted_ebooks
    }), 200

@app.route('/buy-ebook', methods=['POST'])
@require_crypto_webhook
def buy_ebook_webhook():
    """Crypto bot webhook for ebook purchase"""
    data = request.json
    
    telegram_id = data.get('telegram_id')
    ebook_id = data.get('ebook_id')
    amount_usd = data.get('amount_usd')
    
    if not all([telegram_id, ebook_id, amount_usd]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        telegram_id = int(telegram_id)
        ebook_id = int(ebook_id)
        amount_usd = float(amount_usd)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid field types'}), 400
    
    # Get user
    user = get_user(telegram_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Process purchase
    success = purchase_ebook(user['id'], ebook_id, amount_usd)
    
    if success:
        # Add ebook to user's owned list
        GiveawayManager.add_ebook_to_owner(user['id'], ebook_id)
        
        # Check if giveaway should start
        GiveawayManager.check_and_start_giveaway()
        
        updated_user = get_user(telegram_id)
        return jsonify({
            'status': 'success',
            'message': 'Ebook purchased successfully',
            'user': format_user_response(updated_user)
        }), 200
    else:
        return jsonify({'error': 'Failed to process purchase'}), 500

# ==================== GIVEAWAY ENDPOINTS ====================

@app.route('/giveaway/status', methods=['GET'])
def giveaway_status():
    """Get current giveaway status"""
    giveaway = GiveawayManager.get_current_giveaway()
    
    return jsonify({
        'status': 'success',
        'giveaway': giveaway
    }), 200

@app.route('/giveaway/join', methods=['POST'])
def giveaway_join():
    """Join current giveaway"""
    data = request.json or {}
    telegram_id = data.get('telegram_id')
    tickets_to_spend = data.get('tickets', 1)
    
    if not telegram_id:
        return jsonify({'error': 'Missing telegram_id'}), 400
    
    try:
        telegram_id = int(telegram_id)
        tickets_to_spend = int(tickets_to_spend)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid parameters'}), 400
    
    user = get_user(telegram_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    success, message = GiveawayManager.user_join_giveaway(user['id'], tickets_to_spend)
    
    if success:
        updated_user = get_user(telegram_id)
        return jsonify({
            'status': 'success',
            'message': message,
            'user': format_user_response(updated_user)
        }), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/giveaway/end/<int:giveaway_id>', methods=['POST'])
def giveaway_end(giveaway_id):
    """End giveaway and draw winner (admin endpoint)"""
    # In production, verify admin token here
    
    success, result = GiveawayManager.end_giveaway_round(giveaway_id)
    
    if success:
        return jsonify({
            'status': 'success',
            'result': result
        }), 200
    else:
        return jsonify({'error': result}), 500

@app.route('/giveaway/history', methods=['GET'])
def giveaway_history():
    """Get giveaway history"""
    limit = request.args.get('limit', 10, type=int)
    history = GiveawayManager.get_giveaway_history(limit)
    
    formatted_history = [
        {
            'id': g['id'],
            'pool_amount': g['pool_amount'],
            'winner_id': g['winner_id'],
            'ended_at': g['ended_at']
        }
        for g in history
    ]
    
    return jsonify({
        'status': 'success',
        'history': formatted_history
    }), 200

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
