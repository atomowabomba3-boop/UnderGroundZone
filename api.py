from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import random
import time


from database import (
    init_db,
    create_user,
    get_user,
    add_tickets,
    save_language
)



app = FastAPI()



# =========================
# DATABASE
# =========================

init_db()



# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)



# =========================
# MINI APP FILES
# =========================

app.mount(
    "/static",
    StaticFiles(directory="webapp"),
    name="static"
)



@app.get("/app")
async def mini_app():

    return FileResponse(
        "webapp/index.html"
    )



@app.get("/")
async def home():

    return {
        "status":
        "UndergroundZone API running"
    }



# =========================
# MINING SETTINGS
# =========================

MAX_ENERGY = 100

ENERGY_REGEN_TIME = 10

MIN_CLICK_DELAY = 0.7



miners = {}



def get_miner(user_id:int):


    now = time.time()



    if user_id not in miners:

        miners[user_id] = {

            "energy": MAX_ENERGY,

            "last_click": 0,

            "last_update": now

        }



    miner = miners[user_id]



    # regeneracja energii

    passed = now - miner["last_update"]



    recovered = int(
        passed / ENERGY_REGEN_TIME
    )



    if recovered > 0:


        miner["energy"] = min(

            MAX_ENERGY,

            miner["energy"] + recovered

        )


        miner["last_update"] = now



    return miner




# =========================
# USER DATA
# =========================

@app.get("/user/{user_id}")
async def user_data(user_id:int):


    user = get_user(user_id)



    if not user:


        create_user(

            user_id,

            "Telegram User"

        )


        user = get_user(user_id)




    miner = get_miner(user_id)



    return {


        "id":
        user[0],


        "username":
        user[1],


        "language":
        user[2],


        "tickets":
        user[3],


        "gems":
        user[4],


        "level":
        user[5],


        "energy":
        miner["energy"]

    }





# =========================
# MINING
# =========================

@app.post("/mine/{user_id}")
async def mine(user_id:int):


    miner = get_miner(user_id)



    now = time.time()



    # anty autoclicker

    if now - miner["last_click"] < MIN_CLICK_DELAY:


        return {


            "success":
            False,


            "reward":
            0,


            "energy":
            miner["energy"],


            "message":
            "⚠️ Too fast!"

        }




    miner["last_click"] = now




    if miner["energy"] <= 0:


        return {


            "success":
            False,


            "reward":
            0,


            "energy":
            0,


            "message":
            "⚡ No energy!"

        }





    # zużycie energii

    miner["energy"] -= 1





    # 1% szansa na bilet

    if random.random() <= 0.01:



        add_tickets(

            user_id,

            1

        )



        return {


            "success":
            True,


            "reward":
            1,


            "energy":
            miner["energy"],


            "message":
            "💎 Found a ticket! +1 🎟️"

        }





    return {


        "success":
        True,


        "reward":
        0,


        "energy":
        miner["energy"],


        "message":
        "⛏️ Nothing found..."

    }


@app.post("/language/{user_id}/{language}")
async def change_language(
    user_id:int,
    language:str
):

    allowed = [
        "en",
        "pl",
        "de"
    ]


    if language not in allowed:

        return {
            "success":False
        }



    save_language(
        user_id,
        language
    )


    return {

        "success":True,

        "language":language

    }

@app.post("/register/{user_id}")
async def register(user_id:int):


    user = get_user(user_id)


    if not user:

        create_user(
            user_id,
            "Telegram User"
        )


    return {

        "success":True,

        "user_id":user_id

    }

# =========================
# EBOOK STORE
# =========================


ebooks = {

    "tier1": {
        "name":"🟩 Starter Ebook",
        "price":2,
        "tickets":50
    },


    "tier2": {
        "name":"🟦 Advanced Ebook",
        "price":5,
        "tickets":200
    },


    "tier3": {
        "name":"🟪 Ultimate Ebook",
        "price":10,
        "tickets":500
    }

}



@app.get("/ebooks")
async def get_ebooks():

    return ebooks



@app.post("/buy/{user_id}/{tier}")
async def buy_ebook(user_id:int,tier:str):


    if tier not in ebooks:

        return {
            "success":False,
            "message":"Invalid ebook"
        }



    ebook = ebooks[tier]


    add_tickets(
        user_id,
        ebook["tickets"]
    )


    return {

        "success":True,

        "message":
        f"Purchased {ebook['name']} +{ebook['tickets']} tickets"

    }
