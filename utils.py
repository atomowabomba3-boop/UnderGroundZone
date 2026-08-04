import hashlib
import hmac
import json
from functools import wraps
from flask import request, jsonify
import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN', '')

def verify_telegram_web_app(data):
    """
    Verify Telegram Web App authentication
    Returns telegram_id if valid, None otherwise
    """
    try:
        # In production, verify the init_data signature
        # For development, just extract telegram_id
        if 'user' in data:
            user_data = json.loads(data['user']) if isinstance(data['user'], str) else data['user']
            return user_data.get('id')
        return None
    except Exception:
        return None

def verify_crypto_webhook(request_data, signature):
    """
    Verify crypto bot webhook signature
    Returns True if valid
    """
    try:
        message = json.dumps(request_data, sort_keys=True)
        expected_signature = hmac.new(
            CRYPTO_BOT_TOKEN.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False

def require_telegram_id(f):
    """
    Decorator to verify telegram_id in request
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        telegram_id = request.json.get('telegram_id') if request.is_json else request.args.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'error': 'Missing telegram_id'}), 400
        
        try:
            telegram_id = int(telegram_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid telegram_id'}), 400
        
        return f(telegram_id, *args, **kwargs)
    
    return decorated_function

def require_crypto_webhook(f):
    """
    Decorator to verify crypto webhook signature
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get('X-Crypto-Signature')
        
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        if not verify_crypto_webhook(request.json, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def calculate_ticket_value(price):
    """Calculate ticket reward based on price"""
    ticket_map = {
        2: 50,
        5: 150,
        10: 500
    }
    return ticket_map.get(price, 0)

def format_user_response(user_dict):
    """Format user data for API response"""
    if not user_dict:
        return None
    
    return {
        'id': user_dict.get('id'),
        'telegram_id': user_dict.get('telegram_id'),
        'tickets': user_dict.get('tickets', 0),
        'referrals_count': user_dict.get('referrals_count', 0),
        'ebooks_owned': json.loads(user_dict.get('ebooks_owned', '[]')),
        'created_at': user_dict.get('created_at'),
        'updated_at': user_dict.get('updated_at')
    }

def format_ebook_response(ebook_dict):
    """Format ebook data for API response"""
    if not ebook_dict:
        return None
    
    return {
        'id': ebook_dict.get('id'),
        'name': ebook_dict.get('name'),
        'price': ebook_dict.get('price'),
        'tickets_reward': ebook_dict.get('tickets_reward'),
        'file_path': ebook_dict.get('file_path'),
        'cover_image': ebook_dict.get('cover_image')
    }

def get_referral_bonus(referral_count):
    """Get bonus tickets based on referral count milestones"""
    bonuses = {
        5: 5,
        10: 15,
        25: 40,
        50: 100,
        100: 300
    }
    return bonuses.get(referral_count, 0)
