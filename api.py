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
    get_user_ebooks
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
# MINI APP
# =========================


@app.get("/app")
async def mini_app():

    return FileResponse(
        "webapp/index.html"
    )



@app.get("/")
async def home():

    return {
        "status":"UndergroundZone running"
    }





# =========================
# USERS
# =========================


@app.get("/user/{user_id}")
async def user(user_id:int):


    data=get_user(user_id)



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
async def get_ebooks():

    return ebooks





# =========================
# USER EBOOKS
# =========================


@app.get("/myebooks/{user_id}")
async def my_ebooks(user_id:int):


    owned=get_user_ebooks(user_id)


    result=[]


    for ebook in owned:


        if ebook in ebooks:

            result.append(
                ebooks[ebook]
            )


    return result





# =========================
# DOWNLOAD
# =========================


@app.get("/download/{user_id}/{ebook_id}")
async def download(user_id:int,ebook_id:str):


    if not has_ebook(
        user_id,
        ebook_id
    ):

        return {

            "error":
            "You don't own this ebook"

        }



    if ebook_id not in ebooks:

        return {

            "error":
            "Not found"

        }



    return FileResponse(

        "ebooks/" + ebooks[ebook_id]["file"],

        filename=ebooks[ebook_id]["file"]

    )





# =========================
# TEMP BUY TEST
# =========================
# później zastąpi Crypto Pay



@app.post("/testbuy/{user_id}/{ebook_id}")
async def test_buy(user_id:int,ebook_id:str):


    if ebook_id not in ebooks:

        return {
            "success":False
        }



    book=ebooks[ebook_id]



    add_tickets(
        user_id,
        book["tickets"]
    )



    add_ebook(
        user_id,
        ebook_id
    )



    return {

        "success":True,

        "message":
        "Purchased successfully"

    }
