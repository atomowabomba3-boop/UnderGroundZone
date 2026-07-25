import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from database import (
    init_db,
    create_user,
    get_user
)


# =========================
# CONFIG
# =========================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing!")


bot = Bot(TOKEN)
dp = Dispatcher()


# =========================
# DATABASE START
# =========================

init_db()


# =========================
# MAIN MENU
# =========================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⛏️ Mine",
                    callback_data="mine"
                ),
                InlineKeyboardButton(
                    text="👤 Profile",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Giveaway",
                    callback_data="giveaway"
                ),
                InlineKeyboardButton(
                    text="🛒 Store",
                    callback_data="store"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌎 Language",
                    callback_data="language"
                )
            ]
        ]
    )


# =========================
# START COMMAND
# =========================

@dp.message(CommandStart())
async def start(message: types.Message):

    create_user(
        message.from_user.id,
        message.from_user.username
    )

    user = get_user(message.from_user.id)


    text = f"""
⛏️ <b>Welcome to UndergroundZone!</b>

🔥 Underground mining system

🎟️ Tickets:
<b>{user[3]}</b>

💎 Gems:
<b>{user[4]}</b>

⭐ Level:
<b>{user[5]}</b>


Choose your action:
"""


    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================
# HELP
# =========================

@dp.message(Command("help"))
async def help_command(message: types.Message):

    await message.answer(
        """
🤖 <b>UndergroundZone Commands</b>

/start - Open menu
/profile - Your profile
/help - Help

Coming soon:

⛏️ Mining
🎁 Giveaways
🛒 Store
👥 Referral system
🌎 Languages
""",
        parse_mode="HTML"
    )


# =========================
# PROFILE COMMAND
# =========================

@dp.message(Command("profile"))
async def profile(message: types.Message):

    user = get_user(message.from_user.id)

    if not user:
        create_user(
            message.from_user.id,
            message.from_user.username
        )

        user = get_user(message.from_user.id)


    await message.answer(
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

🌎 Language:
<b>{user[2]}</b>
""",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================
# BUTTON HANDLER
# =========================

@dp.callback_query()
async def buttons(callback: CallbackQuery):

    user_id = callback.from_user.id


    if callback.data == "profile":

        user = get_user(user_id)

        await callback.message.edit_text(
            f"""
👤 <b>Your Profile</b>

🎟️ Tickets:
<b>{user[3]}</b>

💎 Gems:
<b>{user[4]}</b>

⭐ Level:
<b>{user[5]}</b>
""",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


    elif callback.data == "mine":

        await callback.answer(
            "⛏️ Mining system is coming soon!",
            show_alert=True
        )


    elif callback.data == "giveaway":

        await callback.message.edit_text(
            """
🎁 <b>Giveaway Center</b>

No active giveaway.

Soon you will be able to join mega giveaways here.
""",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


    elif callback.data == "store":

        await callback.message.edit_text(
            """
🛒 <b>Underground Store</b>

📚 E-books
⚡ Boosts
💎 Gems

Store coming soon.
""",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


    elif callback.data == "language":

        await callback.message.edit_text(
            """
🌎 <b>Select Language</b>

🇬🇧 English
🇵🇱 Polski
🇩🇪 Deutsch
🇪🇸 Español
""",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


    await callback.answer()


# =========================
# START BOT
# =========================

async def main():

    print("🚀 UndergroundZone Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
