import sqlite3


DB_NAME = "underground.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db():

    return sqlite3.connect(DB_NAME)



# =========================
# CREATE TABLES
# =========================

def init_db():

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,

        username TEXT,

        language TEXT DEFAULT 'en',

        tickets INTEGER DEFAULT 1,

        gems INTEGER DEFAULT 0,

        level INTEGER DEFAULT 1

    )
    """)


    conn.commit()
    conn.close()



# =========================
# CREATE USER
# =========================

def create_user(user_id, username):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (
            user_id,
            username
        )

        VALUES (?, ?)
        """,

        (
            user_id,
            username
        )
    )


    conn.commit()
    conn.close()



# =========================
# GET USER
# =========================

def get_user(user_id):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,

        (
            user_id,
        )
    )


    user = cursor.fetchone()


    conn.close()


    return user



# =========================
# CHANGE LANGUAGE
# =========================

def save_language(user_id, language):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE users

        SET language = ?

        WHERE user_id = ?
        """,

        (
            language,
            user_id
        )
    )


    conn.commit()
    conn.close()



# =========================
# ADD TICKETS
# =========================

def add_tickets(user_id, amount):

    conn = get_db()
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



# =========================
# ADD GEMS
# =========================

def add_gems(user_id, amount):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE users

        SET gems = gems + ?

        WHERE user_id = ?
        """,

        (
            amount,
            user_id
        )
    )


    conn.commit()
    conn.close()
