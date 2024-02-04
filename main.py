import logging

from pyrogram import Client
import config
from account import Account
from helpers.database import db
from helpers.db_client import DBClient
import asyncio
from pyrogram import idle
from config import LOGGER
import uvloop
import atexit
from server.routes import web_server
from aiohttp import web

bot = Account()
loop = asyncio.get_event_loop()
server = web.AppRunner(web_server())



class DkClient:
    session: str
    client: Client

    def __init__(self, session: str):
        self.session = session
        self.client = Client(
            name=session,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            device_model="MyKasih",
            app_version="MyKasih 5.0.9",
            system_version=f"MyKasih 5.0.9",
        )


async def init():
    try:
        await bot.start()
        await server.setup()
        await web.TCPSite(server, "0.0.0.0", config.PORT).start()
        logging.info("Service Started at port %s", config.PORT)
        #print("Started Userbot", app.me.first_name)
        await idle()
    except TimeoutError as e:
        print("TimeoutError", e)
    except Exception as e:
        print("Exception", e)
        LOGGER("NpDK").error("Stopping...")


if __name__ == "__main__":
    atexit.register(db.close)
    uvloop.install()
    loop.run_until_complete(init())
    loop.run_until_complete(server.cleanup())
    loop.stop()
    LOGGER("NpDK").info("Stopping! GoodBye")
