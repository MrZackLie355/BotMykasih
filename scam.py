import sys
import os
from pyrogram import Client
from config import (
    API_HASH,
    API_ID,
    LOGGER,
    OWNER,
    BOT_TOKEN,
)

class Scam(Client):
    def __init__(self):
        super().__init__(
            "NpDkBot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={"root": "ext"},
            bot_token=BOT_TOKEN,
        )

        self.LOGGER = LOGGER

    async def start(self):
        try:
            await super().start()
            usr_bot_me = await self.get_me()
            self.username = usr_bot_me.username
            self.namebot = usr_bot_me.first_name
            self.LOGGER(__name__).info(
                f"BOT Started!\n First Name: {self.namebot}\n Username: @{self.username}\n"
            )
        except Exception as a:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            self.LOGGER(__name__).warning(a)
            self.LOGGER(__name__).info("BOT Stopped..")
            sys.exit()

        self.LOGGER(__name__).info(f"BOT RUNNING..")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("BOT stopped.")
