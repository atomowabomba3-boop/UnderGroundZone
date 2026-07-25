import time
import random
import sqlite3


DB_NAME = "underground.db"


# =========================
# ANTI AUTOCLICKER
# =========================

last_clicks = {}

MINING_COOLDOWN = 1.2  # sekundy


# =========================
# DROP SETTINGS
# =========================

# 1% szansy na wykopanie biletu
DROP_CHANCE = 0.001


# =========================
# CHECK CLICK SPEED
# =========================

def can_mine(user_id):

    now = time.time()

    if user_id in last_clicks:

        time_difference = now - last_clicks[user_id]

        if time_difference < MINING_COOLDOWN:

            return False


    last_clicks[user_id] = now

    return True



# =========================
# MINING FUNCTION
# =========================

def mine(user_id):

    # sprawdzanie autoclickera

    if not can_mine(user_id):

        return {
            "success": False,
            "reward": 0,
            "message": "⏳ Too fast! Slow down."
        }


    # losowanie dropu

    chance = random.random()


    if chance <= DROP_CHANCE:

        reward = 1


        add_tickets(
            user_id,
            reward
        )


        return {
            "success": True,
            "reward": reward,
            "message": (
                "💎 Lucky find!\n\n"
                "+1 🎟️ Ticket"
            )
        }


    else:

        return {
            "success": True,
            "reward": 0,
            "message": (
                "⛏️ You mined...\n\n"
                "Nothing found."
            )
        }



# =========================
# ADD TICKETS
# =========================

def add_tickets(user_id, amount):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE users
        SET tickets = tickets + ?
        WHERE user_id = ?
        """,
        (
            amount,
            user_id
        )
    )


    conn.commit()
    conn.close()
