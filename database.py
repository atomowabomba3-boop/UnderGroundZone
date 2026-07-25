import sqlite3


DB_NAME = "underground.db"


def get_db():
    return sqlite3.connect(DB_NAME)



# =========================
# INIT DATABASE
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


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referrals (

        inviter_id INTEGER,

        invited_id INTEGER UNIQUE

    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ebooks (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        ebook_name TEXT

    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mining_history (

        user_id INTEGER,

        time INTEGER

    )
    """)


    conn.commit()
    conn.close()



# =========================
# USERS
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



def get_user(user_id):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,

        (user_id,)
    )


    user = cursor.fetchone()

    conn.close()

    return user



# =========================
# LANGUAGE
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
# TICKETS
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
# GEMS
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



# =========================
# REFERRALS
# =========================

def add_referral(inviter_id, invited_id):

    if inviter_id == invited_id:
        return False


    conn = get_db()
    cursor = conn.cursor()


    try:

        cursor.execute(
            """
            INSERT INTO referrals

            (
                inviter_id,
                invited_id
            )

            VALUES (?,?)

            """,

            (
                inviter_id,
                invited_id
            )
        )


        cursor.execute(
            """
            UPDATE users

            SET tickets = tickets + 1

            WHERE user_id = ?

            """,

            (
                inviter_id,
            )
        )


        conn.commit()

        result = True


    except sqlite3.IntegrityError:

        result = False


    conn.close()


    return result



def get_referrals(user_id):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT COUNT(*)

        FROM referrals

        WHERE inviter_id = ?

        """,

        (
            user_id,
        )
    )


    result = cursor.fetchone()[0]


    conn.close()


    return result



# =========================
# EBOOKS
# =========================

def add_ebook(user_id, ebook_name):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO ebooks

        (
            user_id,
            ebook_name
        )

        VALUES (?,?)

        """,

        (
            user_id,
            ebook_name
        )
    )


    conn.commit()
    conn.close()



def get_ebooks(user_id):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT ebook_name

        FROM ebooks

        WHERE user_id = ?

        """,

        (
            user_id,
        )
    )


    result = cursor.fetchall()


    conn.close()


    return result

def save_language(user_id, language):

    conn = sqlite3.connect("bot_database.db")

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
