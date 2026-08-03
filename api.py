from flask import Flask, request, jsonify, send_from_directory, abort
from database import Database
from utils import load_ebooks, referral_bonus_for_thresholds
from giveaway import GiveawayManager
import os
import requests
import hashlib, hmac
from urllib.parse import parse_qsl

app = Flask(__name__, static_folder='webapp', static_url_path='/')
DB_PATH = os.environ.get('DATABASE_URL', 'database.db')
db = Database(DB_PATH)

essentials = load_ebooks('ebooks')

giveaway = GiveawayManager(db)

# Env / secrets
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # secret expected in webhook headers
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_TELEGRAM_ID = os.environ.get('ADMIN_TELEGRAM_ID', '8998575936')

# verify Telegram init_data according to Telegram docs
def verify_telegram_init_data(bot_token, init_data_str):
    if not bot_token or not init_data_str:
        return False
    params = dict(parse_qsl(init_data_str, keep_blank_values=True))
    hash_received = params.pop('hash', None)
    if not hash_received:
        return False
    # create data_check_string from sorted keys
    data_check_items = [f"{k}={params[k]}" for k in sorted(params.keys())]
    data_check_string = "\n".join(data_check_items)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(hmac_hash, hash_received)

# Health
@app.route('/')
def index():
    return app.send_static_file('index.html')

# small config endpoint for frontend to read admin id
@app.route('/_config', methods=['GET'])
def config():
    return jsonify({'ADMIN_TELEGRAM_ID': ADMIN_TELEGRAM_ID})

# POST /start – rejestracja usera; supports optional init_data verification
@app.route('/start', methods=['POST'])
def start():
    data = request.get_json() or {}
    telegram_id = data.get('telegram_id')
    init_data = data.get('init_data')
    referrer_id = data.get('referrer_id')

    # If init_data provided and bot token available, verify it
    if init_data and TELEGRAM_BOT_TOKEN:
        try:
            ok = verify_telegram_init_data(TELEGRAM_BOT_TOKEN, init_data)
            if not ok:
                return jsonify({'error': 'invalid init_data'}), 403
            # if no telegram_id provided, try extract from init_data
            params = dict(parse_qsl(init_data, keep_blank_values=True))
            if not telegram_id and 'user' in params:
                try:
                    import json
                    u = json.loads(params.get('user'))
                    telegram_id = str(u.get('id')) if u and u.get('id') else telegram_id
                except Exception:
                    pass
        except Exception:
            return jsonify({'error': 'init_data verification failed'}), 403

    if not telegram_id:
        return jsonify({'error': 'telegram_id required'}), 400

    user = db.get_user(telegram_id)
    if user:
        return jsonify({'ok': True, 'user': user})

    # create user with 1 ticket
    db.create_user(telegram_id)

    # if referrer provided, count referral
    if referrer_id:
        db.add_referral(referrer_id, telegram_id)

    user = db.get_user(telegram_id)
    return jsonify({'ok': True, 'user': user}), 201

# GET /me – dane usera
@app.route('/me', methods=['GET'])
def me():
    telegram_id = request.args.get('telegram_id')
    if not telegram_id:
        return jsonify({'error': 'telegram_id required'}), 400
    user = db.get_user(telegram_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    return jsonify({'user': user})

# ... rest of api.py unchanged (routes omitted here for brevity) ...

# Serve static and API routes as before - keep SPA fallback and global 404 handler
def is_api_path(path):
    for p in ['_config', 'ebooks', 'ebook', 'checkout', 'orders', 'admin', 'giveaway', 'send-webapp-button', 'start', 'me', 'referral', 'ranking', 'buy-ebook']:
        if path.startswith(p):
            return True
    return False

@app.route('/<path:path>', methods=['GET'])
def spa_fallback(path):
    if is_api_path(path) or '.' in path:
        return abort(404)
    return app.send_static_file('index.html')

@app.errorhandler(404)
def handle_404(e):
    try:
        p = request.path.lstrip('/')
        if request.method == 'GET' and not is_api_path(p) and '.' not in p:
            return app.send_static_file('index.html'), 200
    except Exception:
        pass
    return e

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
