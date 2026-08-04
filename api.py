from flask import Flask, request, jsonify, abort
import os
import logging

from database import Database
from giveaway import GiveawayManager
from utils import load_ebooks

# --- konfiguracja logowania ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- aplikacja Flask ---
app = Flask(__name__)

# --- DB i manager ---
DB_PATH = os.environ.get("DATABASE_PATH", "database.db")
db = Database(path=DB_PATH)
giveaway = GiveawayManager(db)

# --- konfiguracja przez ENV ---
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", "123")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

# --- endpointy podstawowe ---
@app.route("/_config", methods=["GET"])
def config():
    """Zwraca konfigurację (admin id, dostępne języki)."""
    return jsonify({
        "ADMIN_TELEGRAM_ID": ADMIN_TELEGRAM_ID,
        "default_language": "en",
        "languages": ["en", "pl"]
    })


@app.route("/me", methods=["GET"])
def me():
    """Zwraca info o użytkowniku po telegram_id (query param)."""
    telegram_id = request.args.get("telegram_id")
    if not telegram_id:
        return jsonify({"error": "telegram_id required"}), 400

    user = db.get_user(telegram_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    user = dict(user)
    user["is_admin"] = str(telegram_id) == str(ADMIN_TELEGRAM_ID)
    return jsonify({"user": user})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# --- ebooks ---
@app.route("/ebooks", methods=["GET"])
def list_ebooks():
    items = load_ebooks()
    return jsonify({"ebooks": items})


@app.route("/buy-ebook", methods=["POST"])
def buy_ebook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400
    telegram_id = data.get("telegram_id")
    ebook_id = data.get("ebook_id")
    mode = data.get("mode", "simulate")
    if not telegram_id or ebook_id is None:
        return jsonify({"error": "telegram_id and ebook_id required"}), 400

    # create user if needed
    user = db.get_user(telegram_id)
    if not user:
        db.create_user(telegram_id)

    # lookup ebook price via utils
    ebooks = load_ebooks()
    ebook = next((e for e in ebooks if e.get("id") == int(ebook_id)), None)
    if not ebook:
        return jsonify({"error": "ebook not found"}), 404

    amount_cents = int(float(ebook.get("price_usd", 0)) * 100)
    order_token = db.create_order(telegram_id, ebook_id, amount_cents, mode=mode)

    # if mode is simulate, mark paid immediately for convenience
    if mode == "simulate":
        db.mark_order_paid(order_token)
        db.add_ebook_to_user(telegram_id, int(ebook_id), tickets_awarded=0)

    return jsonify({"order_token": order_token, "amount_cents": amount_cents})


@app.route("/webhook/payment", methods=["POST"])
def payment_webhook():
    # simple webhook that expects X-WEBHOOK-SECRET header to match
    header_secret = request.headers.get("X-WEBHOOK-SECRET")
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not configured")
        return jsonify({"error": "webhook not configured"}), 500
    if header_secret != WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret")
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400
    order_token = data.get("order_token")
    if not order_token:
        return jsonify({"error": "order_token required"}), 400

    order = db.get_order(order_token)
    if not order:
        return jsonify({"error": "order not found"}), 404

    db.mark_order_paid(order_token)
    # grant ebook
    try:
        db.add_ebook_to_user(order["telegram_id"], int(order["ebook_id"]), tickets_awarded=0)
    except Exception:
        logger.exception("Failed to grant ebook for order %s", order_token)

    return jsonify({"ok": True})


# --- giveaway endpoints ---
@app.route("/giveaway/state", methods=["GET"])
def giveaway_state():
    return jsonify(giveaway.get_state())


@app.route("/giveaway/start", methods=["POST"])
def giveaway_start():
    # only admin
    telegram_id = request.get_json(silent=True) and request.get_json().get("telegram_id")
    if str(telegram_id) != str(ADMIN_TELEGRAM_ID):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json(force=True, silent=True) or {}
    duration = data.get("duration_minutes")
    ok = giveaway.start(duration_minutes=duration)
    if not ok:
        return jsonify({"error": "failed to start giveaway (maybe pool too small)"}), 400
    return jsonify({"ok": True})


@app.route("/giveaway/join", methods=["POST"])
def giveaway_join():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400
    telegram_id = data.get("telegram_id")
    cost = int(data.get("cost", 1))
    ok, msg = giveaway.join(telegram_id, cost=cost)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify({"ok": True, "message": msg})


@app.route("/giveaway/end", methods=["POST"])
def giveaway_end():
    # only admin
    data = request.get_json(force=True, silent=True) or {}
    telegram_id = data.get("telegram_id")
    if str(telegram_id) != str(ADMIN_TELEGRAM_ID):
        return jsonify({"error": "forbidden"}), 403
    res = giveaway.end()
    return jsonify(res)


# --- obsługa błędów (przydatne w logs) ---
@app.errorhandler(500)
def handle_500(e):
    logger.exception("Internal server error")
    return jsonify({"error": "internal server error"}), 500


# --- local run (przydatne do testów) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting dev server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
