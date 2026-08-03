# UnderGroundZone - API
# Main Flask application
from flask import Flask, request, jsonify, send_from_directory, abort
from database import Database
from utils import load_ebooks, referral_bonus_for_thresholds
from giveaway import GiveawayManager
import os
import requests

app = Flask(__name__, static_folder='webapp', static_url_path='/')
DB_PATH = os.environ.get('DATABASE_URL', 'database.db')
db = Database(DB_PATH)

essentials = load_ebooks('ebooks')

giveaway = GiveawayManager(db)

# Env / secrets
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # secret expected in webhook headers
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Health
@app.route('/')
def index():
    return app.send_static_file('index.html')

# POST /start – rejestracja usera
@app.route('/start', methods=['POST'])
def start():
    data = request.get_json() or {}
    telegram_id = data.get('telegram_id')
    referrer_id = data.get('referrer_id')
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

# POST /referral – dodanie refa
@app.route('/referral', methods=['POST'])
def referral():
    data = request.get_json() or {}
    referrer = data.get('referrer_id')
    referee = data.get('referee_id')
    if not referrer or not referee:
        return jsonify({'error': 'referrer_id and referee_id required'}), 400
    ok, msg = db.add_referral(referrer, referee)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'ok': True, 'message': msg})

# GET /ranking – top 10
@app.route('/ranking', methods=['GET'])
def ranking():
    top = db.get_ranking(10)
    return jsonify({'ranking': top})

# GET /ebooks – lista ebooków
@app.route('/ebooks', methods=['GET'])
def ebooks_list():
    ebooks = essentials
    return jsonify({'ebooks': ebooks})

# Serve ebook file via backend
@app.route('/ebook/<path:filename>', methods=['GET'])
def serve_ebook(filename):
    ebook_dir = os.path.join(os.getcwd(), 'ebooks')
    if not os.path.exists(os.path.join(ebook_dir, filename)):
        abort(404)
    return send_from_directory(ebook_dir, filename, as_attachment=True)

# POST /buy-ebook – webhook crypto-bota
@app.route('/buy-ebook', methods=['POST'])
def buy_ebook():
    # Webhook should include a secret header 'X-WEBHOOK-SECRET' equal to WEBHOOK_SECRET
    if WEBHOOK_SECRET:
        header_secret = request.headers.get('X-WEBHOOK-SECRET')
        if header_secret != WEBHOOK_SECRET:
            return jsonify({'error': 'invalid webhook secret'}), 403

    data = request.get_json() or {}
    telegram_id = data.get('telegram_id')
    ebook_id = data.get('ebook_id')
    amount = data.get('amount_usd')
    if not telegram_id or ebook_id is None or amount is None:
        return jsonify({'error': 'telegram_id, ebook_id and amount_usd required'}), 400

    ebooks = essentials
    ebook = next((e for e in ebooks if e['id'] == ebook_id), None)
    if not ebook:
        return jsonify({'error': 'ebook not found'}), 404

    if float(amount) < float(ebook['price_usd']):
        return jsonify({'error': 'amount too small'}), 400

    # grant ebook and tickets
    tickets_map = {2:50, 5:150, 10:500}
    tickets_awarded = tickets_map.get(int(ebook['price_usd']), 0)
    db.add_ebook_to_user(telegram_id, ebook_id, tickets_awarded)

    # add to giveaway pool - 80%
    cents = int(round(float(amount) * 100))
    pool_add = int(round(cents * 0.8))
    giveaway.add_to_pool(pool_add)

    return jsonify({'ok': True, 'awarded_tickets': tickets_awarded})

# Endpoint to send a Web App button via the bot (uses TELEGRAM_BOT_TOKEN env var)
@app.route('/send-webapp-button', methods=['POST'])
def send_webapp_button():
    if not TELEGRAM_BOT_TOKEN:
        return jsonify({'error': 'server not configured with TELEGRAM_BOT_TOKEN'}), 500
    data = request.get_json() or {}
    chat_id = data.get('chat_id')
    webapp_url = data.get('webapp_url')
    text = data.get('text', 'Otwórz Mini App')
    if not chat_id or not webapp_url:
        return jsonify({'error': 'chat_id and webapp_url required'}), 400

    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': {
            'inline_keyboard': [
                [ { 'text': text, 'web_app': { 'url': webapp_url } } ]
            ]
        }
    }
    r = requests.post(url, json=payload)
    try:
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'status_code': r.status_code}), 502

# Giveaways
@app.route('/giveaway/start', methods=['POST'])
def giveaway_start():
    data = request.get_json() or {}
    duration_minutes = data.get('duration_minutes')
    # enforce ghost threshold ($15 -> 1500 cents)
    state = giveaway.get_state()
    GHOST_THRESHOLD = 1500
    if state.get('pool_cents', 0) < GHOST_THRESHOLD:
        return jsonify({'error': 'giveaway pool below ghost threshold', 'pool_cents': state.get('pool_cents', 0)}), 400

    started = giveaway.start(duration_minutes)
    if not started:
        return jsonify({'error': 'could not start giveaway'}), 400
    return jsonify({'ok': True, 'giveaway': giveaway.get_state()})

@app.route('/giveaway/join', methods=['POST'])
def giveaway_join():
    data = request.get_json() or {}
    telegram_id = data.get('telegram_id')
    cost = int(data.get('cost', 1))
    if not telegram_id:
        return jsonify({'error': 'telegram_id required'}), 400
    ok, msg = giveaway.join(telegram_id, cost)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'ok': True, 'message': msg})

@app.route('/giveaway/end', methods=['POST'])
def giveaway_end():
    result = giveaway.end()
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
