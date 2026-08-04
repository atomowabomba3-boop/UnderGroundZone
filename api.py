import os
import json
import hmac
import hashlib
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from database import get_conn, init_db, row_to_dict
from utils import load_ebooks_from_meta, sync_ebooks_meta_to_db, PRICE_TO_TICKETS
from giveaway import get_giveaway_state, start_giveaway, join_giveaway, end_giveaway
from pathlib import Path


def create_app():
    app = Flask(__name__, static_folder="webapp", static_url_path="/")
    CORS(app)

    # init DB and sync ebooks metadata
    init_db()
    try:
        sync_ebooks_meta_to_db()
    except Exception:
        # don't fail startup if sync fails; log and continue
        app.logger.exception('ebooks metadata sync failed')

    # env secrets
    CRYPTO_WEBHOOK_SECRET = os.environ.get("CRYPTO_WEBHOOK_SECRET")
    ADMIN_SECRET = os.environ.get("ADMIN_SECRET")

    # helper functions
    def get_user(telegram_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE telegram_id = ?", (str(telegram_id),))
        row = cur.fetchone()
        conn.close()
        return row_to_dict(row)

    def ensure_user(telegram_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (telegram_id, tickets, referrals, ebooks_owned, ref_bonus_level) VALUES (?,1,0,'[]',0)", (str(telegram_id),))
        conn.commit()
        conn.close()
        return get_user(telegram_id)

    def verify_webhook(req):
        """Verify incoming webhook either by HMAC-SHA256 signature header or plain secret header (legacy).
        Accepts:
          - X-Hub-Signature-256: sha256=hex
          - X-WEBHOOK-SECRET: plain secret (legacy)
        """
        if CRYPTO_WEBHOOK_SECRET:
            # Check HMAC signature header first
            sig_header = req.headers.get("X-Hub-Signature-256") or req.headers.get("X-HUB-SIGNATURE") or req.headers.get("X-Signature")
            if sig_header:
                if sig_header.startswith("sha256="):
                    sig = sig_header.split("=", 1)[1]
                else:
                    sig = sig_header
                # compute HMAC on raw body
                raw = req.get_data() or b""
                computed = hmac.new(CRYPTO_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
                return hmac.compare_digest(computed, sig)
            # fallback: plain secret header
            legacy = req.headers.get("X-WEBHOOK-SECRET")
            if legacy and legacy == CRYPTO_WEBHOOK_SECRET:
                return True
            return False
        else:
            # no secret configured, accept (use only for dev)
            return True

    # Admin decorator-ish
    def require_admin(req):
        if not ADMIN_SECRET:
            return False
        header = req.headers.get("X-ADMIN-SECRET") or req.args.get("admin_secret")
        return header == ADMIN_SECRET

    @app.route("/start", methods=["POST"])
    def start():
        data = request.get_json() or {}
        tid = data.get("telegram_id")
        if not tid:
            return jsonify({"error": "telegram_id required"}), 400
        user = get_user(tid)
        if user:
            return jsonify({"ok": True, "user": user})
        ensure_user(tid)
        user = get_user(tid)
        return jsonify({"ok": True, "user": user})

    @app.route("/me", methods=["GET"])
    def me():
        tid = request.args.get("telegram_id")
        if not tid:
            return jsonify({"error": "telegram_id required"}), 400
        user = get_user(tid)
        if not user:
            return jsonify({"error": "user not found"}), 404
        return jsonify({"ok": True, "user": user})

    @app.route("/referral", methods=["POST"])
    def referral():
        data = request.get_json() or {}
        referrer = data.get("referrer_id")
        referred = data.get("referred_id")
        if not referrer or not referred:
            return jsonify({"error": "referrer_id and referred_id required"}), 400
        ensure_user(referrer)
        ensure_user(referred)
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?,?)", (referrer, referred))
        except Exception:
            conn.close()
            return jsonify({"error": "referral already recorded"}), 400
        # increment referrals and add 1 ticket
        cur.execute("UPDATE users SET referrals = referrals + 1, tickets = tickets + 1 WHERE telegram_id = ?", (referrer,))
        cur.execute("SELECT referrals, ref_bonus_level, tickets FROM users WHERE telegram_id = ?", (referrer,))
        row = cur.fetchone()
        referrals = row["referrals"]
        current_level = row["ref_bonus_level"]
        # tiers sorted ascending
        tiers = [(5,5),(10,15),(25,40),(50,100),(100,300)]
        awarded = 0
        new_level = current_level
        for idx, (threshold, bonus) in enumerate(tiers, start=1):
            if referrals >= threshold and current_level < idx:
                awarded += bonus
                new_level = idx
        if awarded > 0:
            cur.execute("UPDATE users SET tickets = tickets + ?, ref_bonus_level = ? WHERE telegram_id = ?", (awarded, new_level, referrer))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "referrer": referrer, "referred": referred, "referrals": referrals, "bonus_awarded": awarded})

    @app.route("/ranking", methods=["GET"])
    def ranking():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT telegram_id, referrals FROM users ORDER BY referrals DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"ok": True, "ranking": [dict(r) for r in rows]})

    @app.route("/ebooks", methods=["GET"])
    def ebooks():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, filename, title, price_usd, tickets_awarded FROM ebooks")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"ok": True, "ebooks": [dict(r) for r in rows]})

    @app.route("/ebooks/<path:filename>", methods=["GET"])
    def serve_ebook(filename):
        ebooks_dir = Path("ebooks")
        safe = ebooks_dir / Path(filename).name
        if safe.exists():
            return send_from_directory(str(ebooks_dir), safe.name, as_attachment=True)
        # Support raw GitHub links stored in ebook metadata
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT filename FROM ebooks WHERE filename = ?", (filename,))
        row = cur.fetchone()
        conn.close()
        abort(404)

    @app.route("/buy-ebook", methods=["POST"])
    def buy_ebook():
        # verify webhook
        if not verify_webhook(request):
            return jsonify({"error": "invalid webhook signature/secret"}), 403
        data = request.get_json() or {}
        tid = data.get("telegram_id")
        ebook_id = data.get("ebook_id")
        amount = data.get("amount_usd")
        if not (tid and ebook_id and amount is not None):
            return jsonify({"error": "telegram_id, ebook_id, amount_usd required"}), 400
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ebooks WHERE id = ?", (ebook_id,))
        ebook = cur.fetchone()
        if not ebook:
            conn.close()
            return jsonify({"error": "ebook not found"}), 404
        expected = float(ebook["price_usd"])
        if abs(expected - float(amount)) > 0.01:
            conn.close()
            return jsonify({"error": "amount does not match ebook price", "expected": expected, "got": amount}), 400
        tickets_awarded = int(ebook["tickets_awarded"])
        try:
            cur.execute("INSERT OR IGNORE INTO users (telegram_id, tickets, referrals, ebooks_owned, ref_bonus_level) VALUES (?,1,0,'[]',0)", (tid,))
            cur.execute("SELECT ebooks_owned FROM users WHERE telegram_id = ?", (tid,))
            row = cur.fetchone()
            owned = []
            try:
                owned = json.loads(row["ebooks_owned"])
            except Exception:
                owned = []
            if ebook_id not in owned:
                owned.append(ebook_id)
            cur.execute("UPDATE users SET tickets = tickets + ?, ebooks_owned = ? WHERE telegram_id = ?", (tickets_awarded, json.dumps(owned), tid))
            add_to_pool = 0.8 * float(amount)
            cur.execute("UPDATE giveaway SET pool_usd = pool_usd + ? WHERE id=1", (add_to_pool,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({"error": "internal error", "detail": str(e)}), 500
        conn.close()
        return jsonify({"ok": True, "telegram_id": tid, "ebook_id": ebook_id, "tickets_awarded": tickets_awarded, "added_pool_usd": add_to_pool})

    @app.route("/giveaway/start", methods=["POST"])
    def giveaway_start():
        # admin only
        if not require_admin(request):
            return jsonify({"error": "admin secret required"}), 403
        res = start_giveaway()
        if "error" in res:
            return jsonify(res), 400
        return jsonify(res)

    @app.route("/giveaway/join", methods=["POST"])
    def giveaway_join():
        data = request.get_json() or {}
        tid = data.get("telegram_id")
        entries = int(data.get("entries", 1))
        if not tid:
            return jsonify({"error": "telegram_id required"}), 400
        res = join_giveaway(tid, entries=entries)
        if "error" in res:
            return jsonify(res), 400
        return jsonify(res)

    @app.route("/giveaway/end", methods=["POST"])
    def giveaway_end():
        # admin only
        if not require_admin(request):
            return jsonify({"error": "admin secret required"}), 403
        res = end_giveaway()
        if "error" in res:
            return jsonify(res), 400
        return jsonify(res)

    # Admin endpoints
    @app.route("/admin/pool", methods=["GET"])
    def admin_pool():
        if not require_admin(request):
            return jsonify({"error": "admin secret required"}), 403
        state = get_giveaway_state()
        return jsonify({"ok": True, "giveaway": state})

    @app.route("/admin/grant", methods=["POST"])
    def admin_grant():
        if not require_admin(request):
            return jsonify({"error": "admin secret required"}), 403
        data = request.get_json() or {}
        tid = data.get("telegram_id")
        tickets = int(data.get("tickets", 0))
        if not tid or tickets <= 0:
            return jsonify({"error": "telegram_id and tickets>0 required"}), 400
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (telegram_id, tickets, referrals, ebooks_owned, ref_bonus_level) VALUES (?,1,0,'[]',0)", (tid,))
        cur.execute("UPDATE users SET tickets = tickets + ? WHERE telegram_id = ?", (tickets, tid))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "telegram_id": tid, "granted": tickets})

    # Debug endpoint: frontend will POST initDataUnsafe here when opened in Telegram
    @app.route('/debug-open', methods=['POST'])
    def debug_open():
        data = request.get_json(silent=True) or {}
        app.logger.info('DEBUG-OPEN payload: %s', json.dumps(data))
        return jsonify({'ok': True, 'received': True})

    # serve frontend
    @app.route('/', methods=['GET'])
    def index():
        return app.send_static_file('index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
