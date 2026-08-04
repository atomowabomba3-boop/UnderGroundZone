from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app)

DB_PATH = 'database.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE NOT NULL,
            tickets INTEGER DEFAULT 1,
            referrals INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('webapp', 'style.css')

@app.route('/app.js')
def app_js():
    return send_from_directory('webapp', 'app.js')

@app.route('/api/start', methods=['POST'])
def start():
    """Register or get user"""
    data = request.json
    telegram_id = data.get('telegram_id')
    
    if not telegram_id or not str(telegram_id).isdigit():
        return jsonify({'error': 'Invalid telegram_id'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            'INSERT INTO users (telegram_id, tickets, referrals) VALUES (?, ?, ?)',
            (str(telegram_id), 1, 0)
        )
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
        user = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'id': user['id'],
        'telegram_id': user['telegram_id'],
        'tickets': user['tickets'],
        'referrals': user['referrals']
    }), 200

@app.route('/api/user/<telegram_id>', methods=['GET'])
def get_user(telegram_id):
    """Get user info"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'telegram_id': user['telegram_id'],
        'tickets': user['tickets'],
        'referrals': user['referrals']
    }), 200

@app.route('/api/referral', methods=['POST'])
def add_referral():
    """Add referral"""
    data = request.json
    referrer_id = data.get('referrer_id')
    referred_id = data.get('referred_id')
    
    if not referrer_id or not referred_id:
        return jsonify({'error': 'Missing IDs'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Increment referrals for referrer
    cursor.execute(
        'UPDATE users SET referrals = referrals + 1, tickets = tickets + 5 WHERE telegram_id = ?',
        (str(referrer_id),)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'}), 200

@app.route('/api/ranking', methods=['GET'])
def ranking():
    """Get top 10 referrers"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT telegram_id, referrals, tickets FROM users ORDER BY referrals DESC LIMIT 10'
    )
    users = cursor.fetchall()
    conn.close()
    
    ranking_list = [
        {
            'rank': i + 1,
            'telegram_id': u['telegram_id'],
            'referrals': u['referrals'],
            'tickets': u['tickets']
        }
        for i, u in enumerate(users)
    ]
    
    return jsonify({'ranking': ranking_list}), 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
