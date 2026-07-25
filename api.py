from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import (
    init_db,
    create_user,
    get_user,
    add_tickets,
    add_ebook,
    has_ebook,
    get_user_ebooks,
    get_active_giveaway,
    already_joined,
    join_giveaway,
    use_tickets_for_giveaway,
    create_giveaway,
    get_participants
)


app = FastAPI()


init_db()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)





# =========================
# FILES
# =========================


app.mount(
    "/static",
    StaticFiles(directory="webapp"),
    name="static"
)


app.mount(
    "/ebooks",
    StaticFiles(directory="ebooks"),
    name="ebooks"
)





# =========================
# APP
# =========================


@app.get("/")
async def home():

    return {
        "status":"UndergroundZone running"
    }



@app.get("/app")
async def mini_app():

    return FileResponse(
        "webapp/index.html"
    )







# =========================
# USER
# =========================


@app.get("/user/{user_id}")
async def user(user_id:int):


    data = get_user(user_id)



    if not data:

        create_user(
            user_id,
            "Telegram User"
        )


        data=get_user(user_id)




    return {

        "id":data[0],

        "username":data[1],

        "language":data[2],

        "tickets":data[3],

        "gems":data[4],

        "level":data[5]

    }







# =========================
# EBOOK STORE
# =========================


ebooks = {


"ebook_1":{

"name":"🟩 Starter Ebook",

"price":2,

"tickets":50,

"image":"/static/images/ebook_green.png.jpg",

"file":"ebook_1.pdf"

},



"ebook_2":{

"name":"🟦 Advanced Ebook",

"price":5,

"tickets":200,

"image":"/static/images/ebook_blue.png.jpg",

"file":"ebook_2.pdf"

},



"ebook_3":{

"name":"🟪 Ultimate Ebook",

"price":10,

"tickets":500,

"image":"/static/images/ebook_purple.png.jpg",

"file":"ebook_3.pdf"

}

}






@app.get("/ebooks")
async def ebook_list():

    return ebooks







@app.get("/myebooks/{user_id}")
async def my_ebooks(user_id:int):


    owned=get_user_ebooks(user_id)


    result=[]


    for ebook_id in owned:

        if ebook_id in ebooks:

            result.append(
                ebooks[ebook_id]
            )


    return result







@app.get("/download/{user_id}/{ebook_id}")
async def download(user_id:int, ebook_id:str):


    if not has_ebook(
        user_id,
        ebook_id
    ):

        return {

            "error":
            "You don't own this ebook"

        }



    return FileResponse(

        "ebooks/"+ebooks[ebook_id]["file"],

        filename=ebooks[ebook_id]["file"]

    )







# =========================
# TEST BUY
# później Crypto Pay
# =========================


@app.post("/testbuy/{user_id}/{ebook_id}")
async def test_buy(user_id:int, ebook_id:str):


    if ebook_id not in ebooks:

        return {
            "success":False
        }



    book=ebooks[ebook_id]



    add_ebook(
        user_id,
        ebook_id
    )


    add_tickets(
        user_id,
        book["tickets"]
    )


    return {

        "success":True,

        "message":
        "Purchased!"

    }








# =========================
# GIVEAWAY
# =========================



@app.get("/giveaway")
async def giveaway():

    giveaway=get_active_giveaway()


    if not giveaway:

        return {

            "active":False

        }



    participants=get_participants(
        giveaway[0]
    )



    return {

        "active":True,

        "id":giveaway[0],

        "prize":giveaway[1],

        "end":giveaway[2],

        "participants":len(participants)

    }








@app.post("/join-giveaway/{user_id}")
async def join(user_id:int):


    giveaway=get_active_giveaway()



    if not giveaway:

        return {

            "success":False,

            "message":
            "No active giveaway"

        }




    giveaway_id=giveaway[0]



    if already_joined(
        user_id,
        giveaway_id
    ):

        return {

            "success":False,

            "message":
            "Already joined"

        }




    tickets=use_tickets_for_giveaway(
        user_id
    )



    join_giveaway(

        user_id,

        giveaway_id,

        tickets+1

    )



    return {

        "success":True,

        "tickets":
        tickets+1,

        "message":
        "Joined giveaway!"

    }







# =========================
# ADMIN TEST
# =========================


@app.post("/create-giveaway")
async def new_giveaway():


    create_giveaway(

        500,

        "2026-08-01"

    )


    return {

        "created":True

    }
