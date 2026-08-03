from flask import Flask, request, jsonify
import os
import logging

# --- konfiguracja logowania ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- aplikacja Flask (musi być zdefiniowana PRZED dekoratorami) ---
app = Flask(__name__)

# --- proste in-memory DB dla testów (podmień na rzeczywiste połączenie) ---
class InMemoryDB:
    def __init__(self):
        # przykładowi użytkownicy; zamień to na prawdziwe źródło danych
        self._users = {
            "123": {"id": "123", "name": "Alice"},
            "456": {"id": "456", "name": "Bob"},
        }

    def get_user(self, telegram_id):
        return self._users.get(str(telegram_id))

db = InMemoryDB()

# --- konfiguracja przez ENV ---
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", "123")

# --- endpointy ---
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

    user = dict(user)  # kopiuj, żeby nie modyfikować DB wprost
    user["is_admin"] = str(telegram_id) == str(ADMIN_TELEGRAM_ID)
    return jsonify({"user": user})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

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
