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
# TRANSLATIONS
# =========================

TEXTS = {

    "en": {

        "welcome": "⛏️ <b>Welcome to UndergroundZone!</b>\n\n🎟️ Tickets: <b>{tickets}</b>\n💎 Gems: <b>{gems}</b>\n⭐ Level: <b>{level}</b>\n\nChoose your action:",

        "profile": "👤 <b>Your Profile</b>\n\n🎟️ Tickets: <b>{tickets}</b>\n💎 Gems: <b>{gems}</b>\n⭐ Level: <b>{level}</b>\n🌎 Language: <b>{language}</b>",

        "language": "🌎 Choose language:",

        "changed": "✅ Language changed!",

        "giveaway": "🎁 <b>Giveaway Center</b>\n\nNo active giveaway yet.",

        "store": "🛒 <b>Underground Store</b>\n\n📚 E-books\n⚡ Boosts\n💎 Gems",

        "mine": "⛏️ Mining..."
    },


    "pl": {

        "welcome": "⛏️ <b>Witaj w UndergroundZone!</b>\n\n🎟️ Bilety: <b>{tickets}</b>\n💎 Diamenty: <b>{gems}</b>\n⭐ Poziom: <b>{level}</b>\n\nWybierz opcję:",

        "profile": "👤 <b>Twój profil</b>\n\n🎟️ Bilety: <b>{tickets}</b>\n💎 Diamenty: <b>{gems}</b>\n⭐ Poziom: <b>{level}</b>\n🌎 Język: <b>{language}</b>",

        "language": "🌎 Wybierz język:",

        "changed": "✅ Język zmieniony!",

        "giveaway": "🎁 <b>Centrum konkursów</b>\n\nBrak aktywnego konkursu.",

        "store": "🛒 <b>Sklep Underground</b>\n\n📚 Ebooki\n⚡ Boosty\n💎 Diamenty",

        "mine": "⛏️ Kopanie..."
    },


    "de": {

        "welcome": "⛏️ <b>Willkommen bei UndergroundZone!</b>\n\n🎟️ Tickets: <b>{tickets}</b>\n💎 Edelsteine: <b>{gems}</b>\n⭐ Level: <b>{level}</b>\n\nWähle eine Option:",

        "profile": "👤 <b>Dein Profil</b>\n\n🎟️ Tickets: <b>{tickets}</b>\n💎 Edelsteine: <b>{gems}</b>\n⭐ Level: <b>{level}</b>\n🌎 Sprache: <b>{language}</b>",

        "language": "🌎 Sprache wählen:",

        "changed": "✅ Sprache geändert!",

        "giveaway": "🎁 <b>Gewinnspiel</b>\n\nKein aktives Gewinnspiel.",

        "store": "🛒 <b>Underground Shop</b>\n\n📚 E-Books\n⚡ Boosts\n💎 Edelsteine",

        "mine": "⛏️ Graben..."
    }

}


def t(lang, key):

    if lang not in TEXTS:
        lang = "en"

    return TEXTS[lang][key]



# =========================
# MENU
# =========================

def main_menu(lang="en"):

    menus = {

        "en": [
            ("⛏️ Mine", "mine"),
            ("👤 Profile", "profile"),
            ("🎁 Giveaway", "giveaway"),
            ("🛒 Store", "store"),
            ("🌎 Language", "language")
        ],

        "pl": [
            ("⛏️ Kopalnia", "mine"),
            ("👤 Profil", "profile"),
            ("🎁 Konkurs", "giveaway"),
            ("🛒 Sklep", "store"),
            ("🌎 Język", "language")
        ],

        "de": [
            ("⛏️ Mine", "mine"),
            ("👤 Profil", "profile"),
            ("🎁 Gewinnspiel", "giveaway"),
            ("🛒 Shop", "store"),
            ("🌎 Sprache", "language")
        ]

    }


    m = menus.get(lang, menus["en"])


    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=m[0][0],
                    callback_data=m[0][1]
                ),

                InlineKeyboardButton(
                    text=m[1][0],
                    callback_data=m[1][1]
                )
            ],

            [
                InlineKeyboardButton(
                    text=m[2][0],
                    callback_data=m[2][1]
                ),

                InlineKeyboardButton(
                    text=m[3][0],
                    callback_data=m[3][1]
                )
            ],

            [
                InlineKeyboardButton(
                    text=m[4][0],
                    callback_data=m[4][1]
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


    await message.answer(

        t(user[2], "welcome").format(
            tickets=user[3],
            gems=user[4],
            level=user[5]
        ),

        reply_markup=main_menu(user[2]),

        parse_mode="HTML"
    )



# =========================
# PROFILE COMMAND
# =========================

@dp.message(Command("profile"))
async def profile(message: types.Message):

    user = get_user(message.from_user.id)


    await message.answer(

        t(user[2], "profile").format(
            tickets=user[3],
            gems=user[4],
            level=user[5],
            language=user[2]
        ),

        reply_markup=main_menu(user[2]),

        parse_mode="HTML"
    )



# =========================
# BUTTONS
# =========================

@dp.callback_query()
async def buttons(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = get_user(user_id)

    lang = user[2]


    if callback.data == "mine":

        result = mine(user_id)

        await callback.answer(
            result["message"],
            show_alert=True
        )


    elif callback.data == "profile":

        user = get_user(user_id)

        await callback.message.edit_text(

            t(user[2], "profile").format(
                tickets=user[3],
                gems=user[4],
                level=user[5],
                language=user[2]
            ),

            reply_markup=main_menu(user[2]),

            parse_mode="HTML"
        )


    elif callback.data == "giveaway":

        await callback.message.edit_text(

            t(lang, "giveaway"),

            reply_markup=main_menu(lang),

            parse_mode="HTML"
        )


    elif callback.data == "store":

        await callback.message.edit_text(

            t(lang, "store"),

            reply_markup=main_menu(lang),

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
            t(lang, "language"),
            reply_markup=keyboard
        )


    elif callback.data.startswith("lang_"):

        new_lang = callback.data.replace(
            "lang_",
            ""
        )


        save_language(
            user_id,
            new_lang
        )


        await callback.message.edit_text(

            t(new_lang, "changed"),

            reply_markup=main_menu(new_lang)
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
