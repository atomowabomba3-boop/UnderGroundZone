from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import random
import time

from database import (
    init_db,
    create_user,
    get_user,
    add_tickets
)


app = FastAPI()


init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# tymczasowo pamięć energii
energy = {}



@app.get("/")
async def home():

    return {
        "status": "UndergroundZone API online"
    }



@app.get("/user/{user_id}")
async def user_data(user_id:int):

    user = get_user(user_id)


    if not user:

        create_user(
            user_id,
            "telegram_user"
        )

        user = get_user(user_id)



    return {

        "id": user[0],

        "tickets": user[3],

        "gems": user[4],

        "level": user[5],

        "energy":
            energy.get(user_id,100)

    }




@app.post("/mine/{user_id}")
async def mine(user_id:int):


    current_energy = energy.get(
        user_id,
        100
    )


    if current_energy <= 0:

        return {

            "success":False,

            "message":
            "No energy"

        }



    energy[user_id] = current_energy - 1



    # 1% szansy

    if random.random() <= 0.01:


        add_tickets(
            user_id,
            1
        )


        return {

            "success":True,

            "reward":1,

            "message":
            "💎 +1 Ticket"

        }



    return {

        "success":True,

        "reward":0,

        "message":
        "⛏️ Nothing found"

    }
