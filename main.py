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
    save_language,
    add_referral,
    get_referrals
)

from mining import mine


# =========================
# CONFIG
# =========================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN missing!")


bot = Bot(TOKEN)
dp = Dispatcher()


# =========================
# DATABASE START
# =========================

init_db()



# =========================
# TRANSLATIONS
# =========================

TEXT = {

    "en": {

        "welcome":
        """
⛏️ <b>Welcome to UndergroundZone!</b>

🎟️ Tickets: <b>{tickets}</b>
💎 Gems: <b>{gems}</b>
⭐ Level: <b>{level}</b>

Choose an option:
""",

        "profile":
        """
👤 <b>Your Profile</b>

🎟️ Tickets: <b>{tickets}</b>
💎 Gems: <b>{gems}</b>
⭐ Level: <b>{level}</b>

👥 Invites: <b>{refs}</b>
🌎 Language: <b>{lang}</b>
""",

        "language":
        "🌎 Choose language:",

        "changed":
        "✅ Language changed!",

        "ref":
        """
👥 <b>Your referral link</b>

🔗 {link}

🎟️ Reward:
+1 ticket for every friend!
"""
    },


    "pl": {

        "welcome":
        """
⛏️ <b>Witaj w UndergroundZone!</b>

🎟️ Bilety: <b>{tickets}</b>
💎 Diamenty: <b>{gems}</b>
⭐ Poziom: <b>{level}</b>

Wybierz opcję:
""",

        "profile":
        """
👤 <b>Twój profil</b>

🎟️ Bilety: <b>{tickets}</b>
💎 Diamenty: <b>{gems}</b>
⭐ Poziom: <b>{level}</b>

👥 Zaproszenia: <b>{refs}</b>
🌎 Język: <b>{lang}</b>
""",

        "language":
        "🌎 Wybierz język:",

        "changed":
        "✅ Język zmieniony!",

        "ref":
        """
👥 <b>Twój link zaproszenia</b>

🔗 {link}

🎟️ Nagroda:
+1 bilet za znajomego!
"""
    }

}



def tr(lang, key):

    if lang not in TEXT:
        lang = "en"

    return TEXT[lang][key]



# =========================
# MENU
# =========================

def menu(lang="en"):

    if lang == "pl":

        return InlineKeyboardMarkup(
            inline_keyboard=[

                [
                    InlineKeyboardButton(
                        text="⛏️ Kopalnia",
                        callback_data="mine"
                    ),

                    InlineKeyboardButton(
                        text="👤 Profil",
                        callback_data="profile"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="🎁 Giveaway",
                        callback_data="giveaway"
                    ),

                    InlineKeyboardButton(
                        text="🛒 Sklep",
                        callback_data="store"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="🌎 Język",
                        callback_data="language"
                    )
                ]

            ]
        )


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


    args = message.text.split()


    if len(args) > 1:

        try:

            inviter = int(args[1])

            add_referral(
                inviter,
                message.from_user.id
            )

        except:
            pass


    user = get_user(
        message.from_user.id
    )


    await message.answer(

        tr(
            user[2],
            "welcome"
        ).format(

            tickets=user[3],
            gems=user[4],
            level=user[5]

        ),

        reply_markup=menu(user[2]),

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


    await message.answer(

        tr(
            user[2],
            "profile"
        ).format(

            tickets=user[3],
            gems=user[4],
            level=user[5],
            refs=get_referrals(
                message.from_user.id
            ),
            lang=user[2]

        ),

        reply_markup=menu(user[2]),

        parse_mode="HTML"

    )



# =========================
# REF LINK
# =========================

@dp.message(Command("ref"))
async def ref(message: types.Message):

    info = await bot.get_me()


    link = (
        f"https://t.me/"
        f"{info.username}"
        f"?start={message.from_user.id}"
    )


    user = get_user(
        message.from_user.id
    )


    await message.answer(

        tr(
            user[2],
            "ref"
        ).format(
            link=link
        ),

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

        await callback.message.edit_text(

            tr(
                lang,
                "profile"
            ).format(

                tickets=user[3],
                gems=user[4],
                level=user[5],
                refs=get_referrals(user_id),
                lang=lang

            ),

            reply_markup=menu(lang),

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
                ]

            ]
        )


        await callback.message.edit_text(
            tr(lang,"language"),
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

            tr(
                new_lang,
                "changed"
            ),

            reply_markup=menu(new_lang)

        )


    elif callback.data == "store":

        await callback.message.edit_text(
            "🛒 Store coming soon...",
            reply_markup=menu(lang)
        )


    elif callback.data == "giveaway":

        await callback.message.edit_text(
            "🎁 Giveaway coming soon...",
            reply_markup=menu(lang)
        )


    await callback.answer()



# =========================
# RUN
# =========================

async def main():

    print("🚀 UndergroundZone started")

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
