from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import random

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
    allow_headers=["*"]
)



# Mini App frontend

app.mount(
    "/static",
    StaticFiles(directory="webapp"),
    name="static"
)



@app.get("/app")
async def app_page():

    return FileResponse(
        "webapp/index.html"
    )



@app.get("/")
async def home():

    return {
        "status": "UndergroundZone API running"
    }



# =========================
# USER DATA
# =========================

@app.get("/user/{user_id}")
async def user(user_id:int):


    data = get_user(user_id)


    if not data:

        create_user(
            user_id,
            "Telegram User"
        )


        data = get_user(user_id)



    return {

        "id": data[0],

        "username": data[1],

        "language": data[2],

        "tickets": data[3],

        "gems": data[4],

        "level": data[5],

        "energy": 100

    }



# =========================
# MINING
# =========================


@app.post("/mine/{user_id}")
async def mine(user_id:int):


    # 1% szansy


    if random.random() <= 0.01:


        add_tickets(
            user_id,
            1
        )


        return {

            "success": True,

            "reward": 1,

            "message":
            "💎 Found a ticket! +1 🎟️"

        }



    return {

        "success": True,

        "reward":0,

        "message":
        "⛏️ Nothing found..."

    }
