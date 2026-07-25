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
    get_user,
    save_language
)

from mining import mine
from languages import get_text


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
# DATABASE
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
# START
# =========================

@dp.message(CommandStart())
async def start(message: types.Message):

    create_user(
        message.from_user.id,
        message.from_user.username
    )

    user = get_user(message.from_user.id)

    language = user[2]


    text = get_text(
        language,
        "welcome"
    ).format(
        tickets=user[3],
        gems=user[4],
        level=user[5]
    )


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

⛏️ Mining
🎁 Giveaways
🛒 Store
🌎 Languages
""",
        parse_mode="HTML"
    )


# =========================
# PROFILE
# =========================

@dp.message(Command("profile"))
async def profile(message: types.Message):

    user = get_user(
        message.from_user.id
    )

    if not user:
        create_user(
            message.from_user.id,
            message.from_user.username
        )

        user = get_user(
            message.from_user.id
        )


    text = get_text(
        user[2],
        "profile"
    ).format(
        tickets=user[3],
        gems=user[4],
        level=user[5],
        language=user[2]
    )


    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================
# BUTTON HANDLER
# =========================

@dp.callback_query()
async def buttons(callback: CallbackQuery):

    user_id = callback.from_user.id


    if callback.data == "mine":

        result = mine(user_id)

        await callback.answer(
            result["message"],
            show_alert=True
        )


    elif callback.data == "profile":

        user = get_user(user_id)


        text = get_text(
            user[2],
            "profile"
        ).format(
            tickets=user[3],
            gems=user[4],
            level=user[5],
            language=user[2]
        )


        await callback.message.edit_text(
            text,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


    elif callback.data == "giveaway":

        await callback.message.edit_text(
            """
🎁 <b>Giveaway Center</b>

No active giveaway yet.

Coming soon...
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

Coming soon...
""",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


    elif callback.data == "language":

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🇬🇧 English",
                        callback_data="lang_en"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🇵🇱 Polski",
                        callback_data="lang_pl"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🇩🇪 Deutsch",
                        callback_data="lang_de"
                    )
                ]
            ]
        )


        await callback.message.edit_text(
            "🌎 Choose language:",
            reply_markup=keyboard
        )


    elif callback.data.startswith("lang_"):

        language = callback.data.replace(
            "lang_",
            ""
        )


        save_language(
            user_id,
            language
        )


        await callback.message.edit_text(
            "✅ Language changed!",
            reply_markup=main_menu()
        )


    await callback.answer()


# =========================
# RUN
# =========================

async def main():

    print("🚀 UndergroundZone Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
