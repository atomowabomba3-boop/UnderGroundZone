import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    CallbackQuery
)

from database import (
    init_db,
    create_user,
    get_user,
    get_referrals
)


# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv("WEBAPP_URL")


if not TOKEN:
    raise Exception("BOT_TOKEN missing")


if not WEBAPP_URL:
    raise Exception("WEBAPP_URL missing")



bot = Bot(
    token=TOKEN
)

dp = Dispatcher()



init_db()



# =========================
# KEYBOARD
# =========================

def main_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⛏️ OPEN MINE",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    text="👤 Profile",
                    callback_data="profile"
                ),

                InlineKeyboardButton(
                    text="🎁 Giveaway",
                    callback_data="giveaway"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📚 Store",
                    callback_data="store"
                )
            ]

        ]
    )



# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: types.Message):


    create_user(
        message.from_user.id,
        message.from_user.username
    )


    user = get_user(
        message.from_user.id
    )


    await message.answer(

        f"""
⛏️ <b>UndergroundZone</b>


Welcome to the mining system!


🎟️ Tickets:
<b>{user[3]}</b>

💎 Gems:
<b>{user[4]}</b>

⭐ Level:
<b>{user[5]}</b>


Start mining below 👇
""",

        reply_markup=main_keyboard(),

        parse_mode="HTML"

    )



# =========================
# TICKETS
# =========================

@dp.message(Command("tickets"))
async def tickets(message: types.Message):

    user = get_user(
        message.from_user.id
    )


    await message.answer(

        f"""
🎟️ Your tickets:

<b>{user[3]}</b>
""",

        parse_mode="HTML"

    )



# =========================
# REFERRAL
# =========================

@dp.message(Command("ref"))
async def referral(message: types.Message):


    bot_info = await bot.get_me()


    link = (
        f"https://t.me/"
        f"{bot_info.username}"
        f"?start={message.from_user.id}"
    )


    refs = get_referrals(
        message.from_user.id
    )


    await message.answer(

        f"""
👥 <b>Your referral system</b>


🔗 Your link:

{link}


👤 Invited:
<b>{refs}</b>


🎟️ Reward:
+1 ticket per person
""",

        parse_mode="HTML"

    )



# =========================
# PROFILE BUTTON
# =========================

@dp.callback_query(
    lambda c: c.data == "profile"
)
async def profile(callback: CallbackQuery):


    user = get_user(
        callback.from_user.id
    )


    await callback.message.edit_text(

        f"""
👤 <b>Your Profile</b>


🆔 ID:
<code>{user[0]}</code>


🎟️ Tickets:
<b>{user[3]}</b>


💎 Gems:
<b>{user[4]}</b>


⭐ Level:
<b>{user[5]}</b>

""",

        reply_markup=main_keyboard(),

        parse_mode="HTML"

    )


    await callback.answer()



# =========================
# PLACEHOLDERS
# =========================

@dp.callback_query(
    lambda c: c.data == "store"
)
async def store(callback: CallbackQuery):

    await callback.message.answer(
        "📚 Store coming soon..."
    )

    await callback.answer()



@dp.callback_query(
    lambda c: c.data == "giveaway"
)
async def giveaway(callback: CallbackQuery):

    await callback.message.answer(
        "🎁 Giveaway system coming soon..."
    )

    await callback.answer()



# =========================
# START BOT
# =========================

async def main():

    print(
        "🚀 UndergroundZone bot started"
    )

    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(main())
