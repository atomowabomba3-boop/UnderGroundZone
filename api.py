from flask import Flask, request, jsonify
from database import get_db, init_db, calc_referral_bonus

app = Flask(__name__)

@app.before_first_request
def setup():
    init_db()

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        return jsonify({"error": "telegram_id_required"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()

    if not user:
        c.execute("INSERT INTO users (telegram_id, tickets, referrals) VALUES (?, ?, ?)", (telegram_id, 1, 0))
        conn.commit()

    return jsonify({"status": "ok"})

@app.route("/me", methods=["GET"])
def me():
    telegram_id = request.args.get("telegram_id")

    if not telegram_id:
        return jsonify({"error": "telegram_id_required"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT tickets, referrals FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()

    if not user:
        return jsonify({"error": "not_found"}), 404

    bonus = calc_referral_bonus(user["referrals"])

    return jsonify({
        "tickets": user["tickets"],
        "referrals": user["referrals"],
        "referral_bonus": bonus
    })

@app.route("/referral", methods=["POST"])
def referral():
    data = request.json
    inviter_id = data.get("inviter_telegram_id")

    if not inviter_id:
        return jsonify({"error": "inviter_telegram_id_required"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("UPDATE users SET tickets = tickets + 1, referrals = referrals + 1 WHERE telegram_id = ?", (inviter_id,))
    conn.commit()

    return jsonify({"status": "ok"})

@app.route("/ranking", methods=["GET"])
def ranking():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT telegram_id, referrals FROM users ORDER BY referrals DESC LIMIT 10")
    rows = [dict(r) for r in c.fetchall()]

    return jsonify(rows)

@app.route("/ebooks", methods=["GET"])
def ebooks():
    return jsonify([
        {"id": 1, "title": "Ebook 1", "price": 2, "tickets": 50},
        {"id": 2, "title": "Ebook 2", "price": 5, "tickets": 150},
        {"id": 3, "title": "Ebook 3", "price": 10, "tickets": 500},
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
