import sqlite3
from datetime import datetime


DB = "database.db"



def connect():
    return sqlite3.connect(DB)





# =========================
# INIT
# =========================


def init_db():

    con = connect()
    cur = con.cursor()



    # USERS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY,

        username TEXT,

        language TEXT DEFAULT 'en',

        tickets INTEGER DEFAULT 1,

        gems INTEGER DEFAULT 0,

        level INTEGER DEFAULT 1

    )
    """)




    # OWNED EBOOKS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ebooks_owned(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        ebook_id TEXT,

        purchased_at TEXT

    )
    """)




    # GIVEAWAY

    cur.execute("""
    CREATE TABLE IF NOT EXISTS giveaway(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        prize REAL,

        end_time TEXT,

        active INTEGER DEFAULT 1

    )
    """)




    # GIVEAWAY ENTRIES

    cur.execute("""
    CREATE TABLE IF NOT EXISTS giveaway_entries(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        giveaway_id INTEGER,

        user_id INTEGER,

        tickets INTEGER,

        joined_at TEXT

    )
    """)




    # WINNERS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS winners(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        giveaway_id INTEGER,

        user_id INTEGER,

        prize REAL,

        date TEXT

    )
    """)



    con.commit()
    con.close()







# =========================
# USERS
# =========================


def create_user(user_id, username):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    INSERT OR IGNORE INTO users
    (id, username)
    VALUES (?,?)
    """,
    (
        user_id,
        username
    )
    )


    con.commit()
    con.close()






def get_user(user_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    SELECT *
    FROM users
    WHERE id=?
    """,
    (user_id,)
    )


    data = cur.fetchone()


    con.close()

    return data






def add_tickets(user_id, amount):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    UPDATE users
    SET tickets=tickets+?
    WHERE id=?
    """,
    (
        amount,
        user_id
    )
    )


    con.commit()
    con.close()






def use_tickets_for_giveaway(user_id):

    con = connect()
    cur = con.cursor()


    # zostawia 1 stały bilet

    cur.execute(
    """
    SELECT tickets
    FROM users
    WHERE id=?
    """,
    (user_id,)
    )


    data = cur.fetchone()


    if not data:
        con.close()
        return 0



    current = data[0]

    used = max(current - 1, 0)



    cur.execute(
    """
    UPDATE users
    SET tickets=1
    WHERE id=?
    """,
    (user_id,)
    )



    con.commit()
    con.close()


    return used







def save_language(user_id, language):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    UPDATE users
    SET language=?
    WHERE id=?
    """,
    (
        language,
        user_id
    )
    )


    con.commit()
    con.close()







# =========================
# EBOOKS
# =========================


def add_ebook(user_id, ebook_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    INSERT INTO ebooks_owned
    (user_id, ebook_id, purchased_at)
    VALUES (?,?,?)
    """,
    (
        user_id,
        ebook_id,
        datetime.now().isoformat()
    )
    )


    con.commit()
    con.close()





def has_ebook(user_id, ebook_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    SELECT id
    FROM ebooks_owned
    WHERE user_id=? AND ebook_id=?
    """,
    (
        user_id,
        ebook_id
    )
    )


    result = cur.fetchone()


    con.close()


    return result is not None





def get_user_ebooks(user_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    SELECT ebook_id
    FROM ebooks_owned
    WHERE user_id=?
    """,
    (user_id,)
    )


    data = cur.fetchall()


    con.close()


    return [x[0] for x in data]







# =========================
# GIVEAWAY
# =========================


def create_giveaway(prize, end_time):

    con = connect()
    cur = con.cursor()


    # wyłącz stare

    cur.execute(
    """
    UPDATE giveaway
    SET active=0
    """
    )


    cur.execute(
    """
    INSERT INTO giveaway
    (prize,end_time,active)
    VALUES (?,?,1)
    """,
    (
        prize,
        end_time
    )
    )


    con.commit()
    con.close()





def get_active_giveaway():

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    SELECT *
    FROM giveaway
    WHERE active=1
    LIMIT 1
    """
    )


    data = cur.fetchone()


    con.close()


    return data





def already_joined(user_id, giveaway_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    SELECT id
    FROM giveaway_entries
    WHERE user_id=? AND giveaway_id=?
    """,
    (
        user_id,
        giveaway_id
    )
    )


    result = cur.fetchone()


    con.close()


    return result is not None





def join_giveaway(user_id, giveaway_id, tickets):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    INSERT INTO giveaway_entries
    (giveaway_id,user_id,tickets,joined_at)
    VALUES (?,?,?,?)
    """,
    (
        giveaway_id,
        user_id,
        tickets,
        datetime.now().isoformat()
    )
    )


    con.commit()
    con.close()






def get_participants(giveaway_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
    """
    SELECT *
    FROM giveaway_entries
    WHERE giveaway_id=?
    """,
    (giveaway_id,)
    )


    data = cur.fetchall()


    con.close()


    return data
