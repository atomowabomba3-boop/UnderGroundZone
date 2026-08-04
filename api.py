from flask import Flask, request, jsonify
from database import init_db, get_conn, row_to_dict
from utils import load_ebooks_from_meta
from flask_cors import CORS
import os
import json
import logging

app = Flask(__name__, static_folder='webapp', static_url_path='/')
CORS(app)

# basic index serves the frontend
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Debug endpoint: frontend will POST initDataUnsafe here when opened inside Telegram
@app.route('/debug-open', methods=['POST'])
def debug_open():
    data = request.get_json(silent=True) or {}
    # Log the payload so you (and I) can inspect what Telegram sent
    app.logger.info('DEBUG-OPEN payload: %s', json.dumps(data))
    return jsonify({'ok': True, 'received': True})

# (Other API endpoints remain unchanged elsewhere in the repo)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
