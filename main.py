import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

from database import (
    init_db,
    create_user,
    get_user
)


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")

bot = Bot(TOKEN)
dp = Dispatcher()


# Start bazy danych
init_db()


@dp.message(CommandStart())
async def start(message: types.Message):

    create_user(
        message.from_user.id,
        message.from_user.username
    )

    user = get_user(message.from_user.id)

    await message.answer(
        f"""
⛏️ <b>Welcome to UndergroundZone!</b>

🎟️ Tickets: <b>{user[3]}</b>
💎 Gems: <b>{user[4]}</b>
⭐ Level: <b>{user[5]}</b>

Choose what you want to do:

⛏️ Mine
🎁 Giveaway
🛒 Store
👤 Profile

Use /help to see commands.
""",
        parse_mode="HTML"
    )


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
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def help_command(message: types.Message):

    await message.answer(
        """
🤖 <b>UndergroundZone Commands</b>

/start - Start bot
/profile - Your profile
/help - Commands

Coming soon:

⛏️ Mining
🎁 Giveaways
🛒 Store
👥 Referrals
🌎 Languages
""",
        parse_mode="HTML"
    )


async def main():

    print("🚀 UndergroundZone Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
