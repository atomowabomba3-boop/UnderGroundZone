import os
import json

THRESHOLDS = [5,10,25,50,100]
THRESHOLD_BONUSES = {5:5, 10:15, 25:40, 50:100, 100:300}


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
