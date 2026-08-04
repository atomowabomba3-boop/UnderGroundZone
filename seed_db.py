"""
seed_db.py

Simple script to initialize database and insert example ebooks and users.
"""
from database import init_db, get_conn
from utils import load_ebooks_from_meta, save_ebook_to_db


def seed():
    init_db()
    ebooks = load_ebooks_from_meta()
    print(f"Found {len(ebooks)} ebooks in ebooks/ebooks.json")
    for eid, meta in ebooks.items():
        record = {
            "id": eid,
            "filename": meta.get("filename"),
            "title": meta.get("title"),
            "price_usd": float(meta.get("price_usd")),
            "tickets_awarded": int(meta.get("tickets_awarded")),
        }
        save_ebook_to_db(record)
    # add example users
    conn = get_conn()
    cur = conn.cursor()
    users = [
        ("1001", 10, 2, '[]', 0),
        ("1002", 5, 1, '[]', 0),
        ("1003", 0, 0, '[]', 0),
    ]
    for u in users:
        cur.execute("INSERT OR IGNORE INTO users (telegram_id, tickets, referrals, ebooks_owned, ref_bonus_level) VALUES (?,?,?,?,?)", u)
    conn.commit()
    conn.close()
    print("Seed completed")

if __name__ == '__main__':
    seed()
