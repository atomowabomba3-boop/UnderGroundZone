import json
from pathlib import Path
from database import get_conn

# Referral progressive bonuses mapping (threshold => bonus tickets)
REF_BONUS_TIERS = [
    (5, 5),
    (10, 15),
    (25, 40),
    (50, 100),
    (100, 300),
]

EBOOKS_FOLDER = Path("ebooks")
EBOOKS_META = EBOOKS_FOLDER / "ebooks.json"

# default giveaway threshold (USD) to allow starting
GIVEAWAY_START_THRESHOLD_USD = 15.0

# Mapping between price USD and tickets awarded (as requested)
PRICE_TO_TICKETS = {
    2.0: 50,
    5.0: 150,
    10.0: 500,
}


def load_ebooks_from_meta():
    if not EBOOKS_META.exists():
        return {}
    try:
        with open(EBOOKS_META, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ebook_to_db(ebook):
    """
    ebook should be dict with keys: id, filename, title, price_usd, tickets_awarded
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO ebooks (id, filename, title, price_usd, tickets_awarded)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ebook["id"], ebook["filename"], ebook["title"], ebook["price_usd"], ebook["tickets_awarded"]),
    )
    conn.commit()
    conn.close()


def sync_ebooks_meta_to_db():
    ebooks = load_ebooks_from_meta()
    for eid, meta in ebooks.items():
        meta_record = {
            "id": eid,
            "filename": meta["filename"],
            "title": meta["title"],
            "price_usd": float(meta["price_usd"]),
            "tickets_awarded": int(meta["tickets_awarded"]),
        }
        save_ebook_to_db(meta_record)
