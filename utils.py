"""
Utility functions for UnderGroundZone
Helper functions for validation and calculations
"""

import re
import os
import json
from datetime import datetime

THRESHOLDS = [5, 10, 25, 50, 100]
THRESHOLD_BONUSES = {5: 5, 10: 15, 25: 40, 50: 100, 100: 300}

def validate_telegram_id(telegram_id):
    """Validate telegram_id format"""
    if not telegram_id:
        return False
    # Telegram IDs are numeric strings
    return str(telegram_id).isdigit() and len(str(telegram_id)) >= 5

def calculate_referral_bonus(referral_count):
    """
    Calculate bonus tickets based on referral milestones
    
    5 refów → +5 biletów
    10 refów → +15 biletów
    25 refów → +40 biletów
    50 refów → +100 biletów
    100 refów → +300 biletów
    """
    return THRESHOLD_BONUSES.get(referral_count, 0)

def referral_bonus_for_thresholds(total_refs):
    """Return the bonus number of tickets to grant if total_refs hits a threshold.
    This function returns the bonus only for thresholds exactly matched by total_refs.
    It is intended to be called after incrementing the ref count."""
    return THRESHOLD_BONUSES.get(total_refs, 0)

def load_ebooks(folder='ebooks'):
    """Load ebooks metadata from ebooks/ebooks.json (recommended) or build simple list from files."""
    meta_path = os.path.join(folder, 'ebooks.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('ebooks', [])
    # fallback: scan pdfs
    items = []
    if not os.path.exists(folder):
        return items
    for idx, fname in enumerate(os.listdir(folder)):
        if fname.lower().endswith('.pdf'):
            items.append({'id': idx, 'title': fname, 'price_usd': 2, 'filename': fname})
    return items

def get_ebook_price_tiers():
    """Get ebook pricing tiers"""
    return {
        '2': 50,      # $2 → 50 tickets
        '5': 150,     # $5 → 150 tickets
        '10': 500     # $10 → 500 tickets
    }

def format_timestamp(timestamp):
    """Format timestamp for API responses"""
    if isinstance(timestamp, str):
        return timestamp
    return timestamp.isoformat() if timestamp else None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def truncate_string(s, max_length=100):
    """Truncate string to max length"""
    if len(s) > max_length:
        return s[:max_length-3] + '...'
    return s

def cents_to_usd(cents):
    """Convert cents to USD"""
    return cents / 100

def usd_to_cents(usd):
    """Convert USD to cents"""
    return int(usd * 100)

def calculate_giveaway_contribution(purchase_amount_usd):
    """Calculate how much from purchase goes to giveaway pool (80%)"""
    return purchase_amount_usd * 0.80

def get_current_timestamp():
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()

def is_valid_file_path(file_path):
    """Validate file path for ebook PDFs"""
    if not file_path:
        return False
    # Check if it ends with .pdf
    return file_path.lower().endswith('.pdf')
