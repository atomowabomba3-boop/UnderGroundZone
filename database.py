import sqlite3


DB = "database.db"



def connect():

    return sqlite3.connect(DB)




# =========================
# INIT DATABASE
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

        tickets INTEGER DEFAULT 0,

        gems INTEGER DEFAULT 0,

        level INTEGER DEFAULT 1

    )
    """)



    # PURCHASED EBOOKS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ebooks_owned(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        ebook_id TEXT,

        purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)



    # PAYMENTS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        payment_id TEXT,

        ebook_id TEXT,

        status TEXT DEFAULT 'pending'

    )
    """)



    # GIVEAWAY USED TICKETS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS giveaway_entries(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        giveaway_id TEXT,

        tickets_used INTEGER

    )
    """)



    con.commit()

    con.close()






# =========================
# USERS
# =========================



def create_user(user_id, username):


    con=connect()

    cur=con.cursor()



    cur.execute(
    """
    INSERT OR IGNORE INTO users
    (id,username)
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


    con=connect()

    cur=con.cursor()


    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )


    data=cur.fetchone()


    con.close()


    return data






def add_tickets(user_id, amount):


    con=connect()

    cur=con.cursor()


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






def remove_tickets(user_id, amount):


    con=connect()

    cur=con.cursor()


    cur.execute(
    """
    UPDATE users
    SET tickets=tickets-?
    WHERE id=?
    """,
    (
        amount,
        user_id
    )
    )


    con.commit()

    con.close()






def save_language(user_id, language):


    con=connect()

    cur=con.cursor()


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


    con=connect()

    cur=con.cursor()



    cur.execute(
    """
    INSERT INTO ebooks_owned
    (user_id, ebook_id)
    VALUES (?,?)
    """,
    (
        user_id,
        ebook_id
    )
    )


    con.commit()

    con.close()






def has_ebook(user_id, ebook_id):


    con=connect()

    cur=con.cursor()



    cur.execute(
    """
    SELECT id FROM ebooks_owned
    WHERE user_id=? AND ebook_id=?
    """,
    (
        user_id,
        ebook_id
    )
    )


    result=cur.fetchone()


    con.close()


    return result is not None





def get_user_ebooks(user_id):


    con=connect()

    cur=con.cursor()



    cur.execute(
    """
    SELECT ebook_id
    FROM ebooks_owned
    WHERE user_id=?
    """,
    (user_id,)
    )


    data=cur.fetchall()


    con.close()


    return [
        x[0]
        for x in data
    ]







# =========================
# PAYMENTS
# =========================




def create_payment(user_id,payment_id,ebook_id):


    con=connect()

    cur=con.cursor()


    cur.execute(
    """
    INSERT INTO payments
    (user_id,payment_id,ebook_id)
    VALUES (?,?,?)
    """,
    (
        user_id,
        payment_id,
        ebook_id
    )
    )


    con.commit()

    con.close()






def complete_payment(payment_id):


    con=connect()

    cur=con.cursor()


    cur.execute(
    """
    UPDATE payments
    SET status='paid'
    WHERE payment_id=?
    """,
    (payment_id,)
    )


    con.commit()

    con.close()







def get_payment(payment_id):


    con=connect()

    cur=con.cursor()


    cur.execute(
    """
    SELECT *
    FROM payments
    WHERE payment_id=?
    """,
    (payment_id,)
    )


    data=cur.fetchone()


    con.close()


    return data







# =========================
# GIVEAWAYS
# =========================




def enter_giveaway(user_id,giveaway_id,amount):


    remove_tickets(
        user_id,
        amount
    )


    con=connect()

    cur=con.cursor()


    cur.execute(
    """
    INSERT INTO giveaway_entries
    (user_id,giveaway_id,tickets_used)
    VALUES (?,?,?)
    """,
    (
        user_id,
        giveaway_id,
        amount
    )
    )


    con.commit()

    con.close()
