from account import Account
import asyncio
from pyrogram import idle
from helpers.database import DB
from config import LOGGER
import uvloop
from pyromod import Client, Message
import config

bot = Account()
loop = asyncio.get_event_loop()
db = DB()

async def init():
    try:
        await bot.start()
        await idle()
    except TimeoutError as e:
        print("TimeoutError", e)
    except Exception as e:
        LOGGER("NpDK").error("Stopping...")


if __name__ == "__main__":
    uvloop.install()
    loop.run_until_complete(init())
    LOGGER("NpDK").info("Stopping! GoodBye")
