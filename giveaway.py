import random
from database import get_conn, row_to_dict
from utils import GIVEAWAY_START_THRESHOLD_USD

def get_giveaway_state():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM giveaway WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

def start_giveaway():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pool_usd FROM giveaway WHERE id=1")
    pool = cur.fetchone()["pool_usd"]
    if pool < GIVEAWAY_START_THRESHOLD_USD:
        conn.close()
        return {"error": "giveaway pool below threshold", "pool_usd": pool}
    cur.execute("UPDATE giveaway SET active=1 WHERE id=1")
    conn.commit()
    conn.close()
    return {"ok": True, "pool_usd": pool}

def join_giveaway(telegram_id, entries=1):
    conn = get_conn()
    cur = conn.cursor()
    # deduct tickets from user
    cur.execute("SELECT tickets FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "user not found"}
    tickets = row["tickets"]
    cur.execute("SELECT entry_cost_tickets FROM giveaway WHERE id=1")
    cost = cur.fetchone()["entry_cost_tickets"]
    total_cost = cost * entries
    if tickets < total_cost:
        conn.close()
        return {"error": "not enough tickets", "needed": total_cost, "have": tickets}
    # deduct tickets
    cur.execute("UPDATE users SET tickets = tickets - ? WHERE telegram_id = ?", (total_cost, telegram_id))
    # add or update participant entry count
    cur.execute("SELECT id, entries FROM giveaway_participants WHERE telegram_id = ?", (telegram_id,))
    p = cur.fetchone()
    if p:
        cur.execute("UPDATE giveaway_participants SET entries = entries + ? WHERE telegram_id = ?", (entries, telegram_id))
    else:
        cur.execute("INSERT INTO giveaway_participants (telegram_id, entries) VALUES (?,?)", (telegram_id, entries))
    conn.commit()
    conn.close()
    return {"ok": True, "spent": total_cost}

def end_giveaway():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, entries FROM giveaway_participants")
    parts = cur.fetchall()
    if not parts:
        cur.execute("UPDATE giveaway SET active=0, pool_usd=0 WHERE id=1")
        conn.commit()
        conn.close()
        return {"error": "no participants"}
    # build weighted list
    weighted = []
    for p in parts:
        weighted.extend([p["telegram_id"]] * max(1, int(p["entries"])))
    winner = random.choice(weighted)
    # reset participant tickets to 1
    # fetch participants unique ids
    telegram_ids = [p["telegram_id"] for p in parts]
    for tid in telegram_ids:
        cur.execute("UPDATE users SET tickets = 1 WHERE telegram_id = ?", (tid,))
    # clear participants
    cur.execute("DELETE FROM giveaway_participants")
    # reset pool and active flag
    cur.execute("UPDATE giveaway SET active=0, pool_usd=0 WHERE id=1")
    conn.commit()
    conn.close()
    return {"ok": True, "winner": winner}
