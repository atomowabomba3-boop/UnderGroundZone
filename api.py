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

# Helper to determine public frontend base used in referral links
def get_frontend_base():
    # Prefer explicit environment variable (set this to your public webapp URL, e.g. https://your-app.example)
    env = os.getenv('FRONTEND_URL') or os.getenv('FRONTEND_BASE') or os.getenv('WEBAPP_URL')
    if env:
        return env.rstrip('/')
    # Fallback to request.host_url when in request context (may be Telegram proxy -> not desired)
    try:
        return request.host_url.rstrip('/')
    except RuntimeError:
        return ''

# Helper to build referral link; prefer bot deep-link with a 'ref:' payload so
# Telegram passes start_param that we can parse.
# Example: https://t.me/udrgroundbot?start=ref:48485992
def build_referral_link(telegram_id):
    bot_username = os.getenv('BOT_USERNAME') or os.getenv('TELEGRAM_BOT_USERNAME') or 'UdrgroundBot'
    if bot_username:
        try:
            return f"https://t.me/{bot_username}?start=ref:{int(telegram_id)}"
        except Exception:
            # fallback to string interpolation if id not int-castable
            return f"https://t.me/{bot_username}?start=ref:{telegram_id}"

    # Fallback to frontend link only if bot username missing
    frontend_base = get_frontend_base()
    if frontend_base:
        return f"{frontend_base}/?ref={telegram_id}"

    try:
        return f"{request.host_url.rstrip('/')}/?ref={telegram_id}"
    except RuntimeError:
        return None

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
    The referrer_telegram_id can be either a bare numeric id or a string payload like 'ref:12345' coming from
    Telegram deep-link start parameter. We robustly parse both forms here.
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
                    # Accept 'ref:12345', 'start=ref:12345', or plain numeric
                    if isinstance(referrer_id, str):
                        rid = referrer_id
                        if rid.startswith('start='):
                            rid = rid.split('=', 1)[1]
                        if rid.startswith('ref:'):
                            rid = rid.split(':', 1)[1]
                        referrer_id = int(rid)
                    else:
                        referrer_id = int(referrer_id)

                    # Don't allow self-referral
                    if referrer_id != telegram_id:
                        add_referral(referrer_id, telegram_id)
                except Exception:
                    # ignore invalid referrer values
                    pass
        
        # Build response and include referral link for this user
        user_resp = format_user_response(user)
        user_resp['referral_link'] = build_referral_link(user_resp.get('telegram_id'))
        
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
    user_resp['referral_link'] = build_referral_link(user_resp.get('telegram_id'))
    
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
        # support 'ref:123' forms here too
        if isinstance(referrer_telegram_id, str) and referrer_telegram_id.startswith('ref:'):
            referrer_telegram_id = int(referrer_telegram_id.split(':', 1)[1])
        else:
            referrer_telegram_id = int(referrer_telegram_id)

        referred_telegram_id = int(referred_telegram_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid telegram_ids'}), 400
    
    success = add_referral(referrer_telegram_id, referred_telegram_id)
    
    if success:
        referrer = get_user(referrer_telegram_id)
        ref_resp = format_user_response(referrer)
        ref_resp['referral_link'] = build_referral_link(ref_resp.get('telegram_id'))
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
        user_resp['referral_link'] = build_referral_link(user_resp.get('telegram_id'))
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

