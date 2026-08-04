from flask import Flask, request, jsonify, send_from_directory, make_response, abort, current_app
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests

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

# Serve the frontend from the `webapp/` directory
base_dir = os.path.dirname(__file__)
static_dir = os.path.join(base_dir, 'webapp')
app = Flask(__name__, static_folder=static_dir, static_url_path='')
CORS(app)

# Serve index at root so Telegram Web App gets the front page
@app.route('/')
def index():
    index_path = os.path.join(static_dir, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(static_dir, 'index.html')
    return jsonify({'error': 'Endpoint not found'}), 404

# Explicitly serve common static assets to avoid Flask static resolution issues
@app.route('/app.js', methods=['GET'])
def serve_app_js():
    file_path = os.path.join(static_dir, 'app.js')
    if os.path.isfile(file_path):
        return send_from_directory(static_dir, 'app.js')
    return jsonify({'error': 'Endpoint not found'}), 404

@app.route('/style.css', methods=['GET'])
def serve_style_css():
    file_path = os.path.join(static_dir, 'style.css')
    if os.path.isfile(file_path):
        return send_from_directory(static_dir, 'style.css')
    return jsonify({'error': 'Endpoint not found'}), 404

# Initialize database on startup
with app.app_context():
    try:
        init_db()
    except Exception:
        # If DB init fails, don't crash the whole app — log and continue so health checks work
        import traceback
        traceback.print_exc()

# ==================== USER ENDPOINTS ====================

@app.route('/start', methods=['POST'])
def start():
    """Register new user or return existing user

    Accepts optional 'referrer_telegram_id' in JSON payload to record a referral when a new user signs up.
    """
    try:
        data = request.json or {}
        telegram_id = data.get('telegram_id')
        referrer_id = data.get('referrer_telegram_id')
        
        if not telegram_id:
            return jsonify({'error': 'Missing telegram_id'}), 400
        
        try:
            telegram_id = int(telegram_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid telegram_id'}), 400
        
        # Check if user exists
        user = get_user(telegram_id)
        created = False
        if not user:
            # Create new user
            user = create_user(telegram_id)
            created = True
            if not user:
                return jsonify({'error': 'Failed to create user'}), 500

            # If referrer provided, attempt to record referral
            if referrer_id:
                try:
                    referrer_id = int(referrer_id)
                    # Don't allow self-referral
                    if referrer_id != telegram_id:
                        add_referral(referrer_id, telegram_id)
                except Exception:
                    # ignore invalid referrer
                    pass
        
        # Build response and include referral link for this user
        user_resp = format_user_response(user)
        try:
            user_resp['referral_link'] = f"{request.host_url.rstrip('/')}?ref={user_resp.get('telegram_id')}"
        except Exception:
            user_resp['referral_link'] = None
        
        return jsonify({
            'status': 'success',
            'user': user_resp,
            'created': created
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

@app.route('/me', methods=['GET'])
@require_telegram_id
def get_me(telegram_id):
    """Get current user data"""
    user = get_user(telegram_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_resp = format_user_response(user)
    try:
        user_resp['referral_link'] = f"{request.host_url.rstrip('/')}?ref={user_resp.get('telegram_id')}"
    except Exception:
        user_resp['referral_link'] = None
    
    return jsonify({
        'status': 'success',
        'user': user_resp
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
        ref_resp = format_user_response(referrer)
        try:
            ref_resp['referral_link'] = f"{request.host_url.rstrip('/')}?ref={ref_resp.get('telegram_id')}"
        except Exception:
            ref_resp['referral_link'] = None
        return jsonify({
            'status': 'success',
            'message': 'Referral added',
            'referrer': ref_resp
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


@app.route('/download/<path:filename>', methods=['GET'])
def download_ebook(filename):
    """Serve ebook files.

    Tries to serve from local /ebooks directory first. If not found,
    proxies the file from GitHub raw (GITHUB_RAW_BASE) and returns it
    with CORS header so it can be fetched from the Web App.
    """
    # Local ebooks directory
    ebooks_dir = os.path.join(base_dir, 'ebooks')
    local_path = os.path.join(ebooks_dir, filename)

    # Security: prevent path traversal
    if '..' in filename or filename.startswith('/'):
        abort(400)

    if os.path.isfile(local_path):
        resp = make_response(send_from_directory(ebooks_dir, filename, as_attachment=True))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # Proxy from GitHub raw
    raw_base = current_app.config.get('GITHUB_RAW_BASE', 'https://raw.githubusercontent.com/atomowabomba3-boop/UnderGroundZone/main/ebooks')
    raw_url = f"{raw_base}/{filename}"
    r = requests.get(raw_url, stream=True)
    if r.status_code != 200:
        abort(404)

    resp = make_response(r.content)
    resp.headers['Content-Type'] = r.headers.get('Content-Type', 'application/pdf')
    resp.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


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
        user_resp = format_user_response(updated_user)
        try:
            user_resp['referral_link'] = f"{request.host_url.rstrip('/')}?ref={user_resp.get('telegram_id')}"
        except Exception:
            user_resp['referral_link'] = None
        return jsonify({
            'status': 'success',
            'message': 'Ebook purchased successfully',
            'user': user_resp
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

@app.route('/giveaway/start', methods=['POST'])
def giveaway_start():
    """Admin endpoint to start a giveaway manually if none active"""
    data = request.json or {}
    admin_id = data.get('admin_telegram_id') or request.headers.get('X-Admin-Telegram')

    if admin_id is None:
        return jsonify({'error': 'Missing admin id'}), 403
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid admin id'}), 403

    if admin_id != 8998575936:
        return jsonify({'error': 'Forbidden'}), 403

    started = GiveawayManager.check_and_start_giveaway()
    if started:
        return jsonify({'status': 'success', 'message': 'Giveaway started'}), 200
    else:
        return jsonify({'status': 'no_action', 'message': 'Giveaway already active or pool insufficient'}), 200

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
        user_resp = format_user_response(updated_user)
        try:
            user_resp['referral_link'] = f"{request.host_url.rstrip('/')}?ref={user_resp.get('telegram_id')}"
        except Exception:
            user_resp['referral_link'] = None
        return jsonify({
            'status': 'success',
            'message': message,
            'user': user_resp
        }), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/giveaway/end/<int:giveaway_id>', methods=['POST'])
def giveaway_end(giveaway_id):
    """End giveaway and draw winner (admin endpoint)"""
    data = request.json or {}
    admin_id = data.get('admin_telegram_id') or request.headers.get('X-Admin-Telegram')

    if admin_id is None:
        return jsonify({'error': 'Missing admin id'}), 403

    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid admin id'}), 403

    if admin_id != 8998575936:
        return jsonify({'error': 'Forbidden'}), 403

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
    return jsonify({'status':'ok'}), 200

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
