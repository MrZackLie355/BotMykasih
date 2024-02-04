import random
import re
import traceback
from datetime import datetime
from pyrogram.types import Message

import config
from config import (
    API_HASH,
    API_ID,
)
import sys, os
from pyrogram.raw.types.input_peer_user import InputPeerUser
from pyrogram.raw.types import input_report_reason_other
from pyrogram.raw.types import input_peer_user, input_peer_channel, input_peer_chat, ChannelParticipantsSearch, \
    ChannelParticipantsRecent
from pyrogram.enums import ChatType
from pyrogram import Client
import platform
import asyncio
from pyrogram import raw
from pyrogram.raw.functions import account, channels, messages
from pyrogram.raw.functions.auth import reset_authorizations
from pyrogram.raw.types import CodeSettings, send_message_upload_audio_action, InputUser, InputChannel
from pyrogram import types, filters
from pyrogram.errors import (
    AuthKeyUnregistered,
    FreshResetAuthorisationForbidden,
    PeerIdInvalid,
    FloodWait,
    PhoneNumberBanned,
    PhoneNumberInvalid,
    PhoneNumberOccupied,
    PhoneNumberFlood,
    UserDeactivated,
    UserDeactivatedBan, AuthKeyDuplicated, UserAlreadyParticipant, UserPrivacyRestricted, UserNotMutualContact,
    UserChannelsTooMuch,
    PeerFlood, UserKicked, ChatAdminRequired, UserBannedInChannel, ChatWriteForbidden, ChatIdInvalid, ChannelInvalid
)
import csv
import pytz
from helpers.db_client import db_client as client_db


class NpClient:
    def __init__(self, user="", db =None):
        self.db = db
        self.clientdb = client_db
        self.user = user
        self.tz = pytz.timezone("Asia/Jakarta")

    async def init(self, client: Client, msg: Message, show=True):
        self.msg = msg
        self.client = client
        self.id = self.user['idtele']
        id = self.user['idtele']
        self.name = f"Account-{id}"
        self.np = Client(
            name=self.name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=self.user['string_session'],
            in_memory=True,
            app_version="5.0.9",
            device_model="TempDevice",
            system_version="TempDevice 5.0.9",
        )
        try:
            await self.np.start()
            self.me = await self.np.get_me()
            self.idacc = self.me.id
            await asyncio.sleep(2)
            return self.me
        except FloodWait as e:
            await self.msg.reply_text(f"FloodWait {e}")
            await asyncio.sleep(e.value)
        except AuthKeyDuplicated as ea:
            print(self.id, ea)
            await self.db.delete(id)
            return False
        except AuthKeyUnregistered as ea:
            if show:
                await self.msg.reply_text(f"Error: Session telah dihapus, \n{ea}")
            await self.db.delete(id)
            return None
        except UserDeactivatedBan as ea:
            if show:
                await self.msg.reply_text(f"Error: Akun deactivated ban, \n{ea}")
            await self.db.delete(id, True)
            return None
        except UserDeactivated as ea:
            if show:
                await self.msg.reply_text(f"Error: Akun deactivated, \n{ea}")
            await self.db.delete(id, True)
            return None
        except Exception as ex:
            await self.db.delete(id)
            print(ex, "kontol")
            if show:
                await self.msg.reply_text(f"Failed to start client\n{ex}")
            return None

    async def getMyChannel(self):
        try:
            channel = []
            async for dialog in self.np.get_dialogs():
                print(dialog.chat.title or dialog.chat.first_name)
                if dialog.chat.is_creator:
                    channel.append(dialog.chat)
            return channel
        except Exception as e:
            print(e)
            return []

    async def reset_password(self):
        try:
            reset = await self.np.invoke(
                raw.functions.account.reset_password.ResetPassword()
            )
            if isinstance(reset, raw.types.account.ResetPasswordFailedWait):
                datetime_object = datetime.fromtimestamp(reset.retry_date)
                await self.msg.reply_text(f"Gagal reset password, ulagi lagi **{datetime_object.strftime('%Y-%m-%d %H:%M:%S')}**")
            elif isinstance(reset, raw.types.account.ResetPasswordRequestedWait):
                datetime_object = datetime.fromtimestamp(reset.until_date)
                await self.msg.reply_text(f"Berhasil request reset password, tunggu sampai **{datetime_object.strftime('%Y-%m-%d %H:%M:%S')}**")
            else:
                await self.msg.reply_text(f"Done, password has been reset")
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")

    async def read_code(self):
        try:
            pesan = "**CODE**: `{code}`\n**DATE**: {date}"
            code = 0
            date = 0
            msg_id = 0
            async for message in self.np.get_chat_history(777000, limit=5):
                is_code = re.search(r"(\d{5})", message.text)
                if is_code:
                    if message.id > msg_id:
                        msg_id = message.id
                        date = message.date
                        code = is_code.group(1)

            return await self.msg.reply_text(pesan.format(code=code, date=date))
        except Exception as e:
            print(e)
            return False

    async def updateTime(self):
        ses = await self.list_sessions()
        timeLogged = 0
        for s in ses:
            if s.current:
                await self.db.updateTime(self.idacc, s.date_created)
                timeLogged = s.date_created
                break
        return timeLogged

    async def join(self, link):
        try:
            await self.np.join_chat(link)
            return True
        except Exception as e:
            print(e)
            return False

    async def leave(self, link):
        try:
            await self.np.resolve_peer(link)
            await self.np.leave_chat(link)
            return True
        except Exception as e:
            print(e)
            return False

    async def clear_chat2(self, chat):
        try:
            peer = await self.np.resolve_peer(chat)
            delete = await self.np.invoke(
                raw.functions.messages.delete_history.DeleteHistory(
                    peer=peer, max_id=0, just_clear=True, revoke=False
                )
            )
            return True
        except Exception as e:
            print(e)
            return False

    async def send_msg(self, chat, msg):
        try:
            #msgg = await self.np.get_messages("babunyakhenji", 3)
            #peer = await self.np.resolve_peer(msgg.forward_from.id)
            peer = await self.np.resolve_peer(chat)
            await self.np.send_message(chat, msg)
            return True
        except Exception as e:
            print(e)
            return False

    async def reaction(self, chat, msgid, react):
        try:
            await self.np.send_reaction(chat, msgid, react)
            return True
        except Exception as e:
            print(e)
            return False

    async def changeName(self, name):
        try:
            await self.np.update_profile(first_name=name)
            await self.msg.reply_text("Done, name has been changed")
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")

    async def keluar(self):
        try:
            await self.np.log_out()
            return True
        except Exception as e:
            print(e)
            return False
    async def reset_session(self, hash):
        try:
            await self.np.invoke(
                account.reset_authorization.ResetAuthorization(hash=int(hash))
            )
            await self.msg.reply_text("Done, specific session has terminate")
        except FreshResetAuthorisationForbidden as e:
            print(e)
            await self.msg.reply_text(
                "Tidak bisa menghapus session, belum 24jam logged"
            )
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")

    async def reset_sessions(self):
        try:
            list_session = await self.np.invoke(
                account.get_authorizations.GetAuthorizations()
            )
            #await self.np.invoke(reset_authorizations.ResetAuthorizations())
            list_msg = ""
            for ls in list_session.authorizations:
                if "POCO F1" not in ls.device_model:
                    if not ls.current:
                        await self.np.invoke(
                            account.reset_authorization.ResetAuthorization(hash=int(ls.hash))
                        )
                if not ls.current:
                    list_msg += f"{ls.device_model}\n"
            list_msg += f"\n{len(list_session.authorizations) -1} terminate"
            await self.msg.reply_text(
                list_msg,
            )
            await self.msg.reply_text("Done, all session has terminate except current")
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")

    async def list_sessions(self):
        try:
            list_session = await self.np.invoke(
                account.get_authorizations.GetAuthorizations()
            )
            sessions = list()
            for auth in list_session.authorizations:
                print(auth.device_model)
                if "POCO F1" in auth.device_model:
                    continue
                sessions.append(auth)
            return sessions
        except AuthKeyUnregistered as ea:
            await self.msg.reply_text(f"Error: {ea}")
            await self.db.delete(self.idacc)
        except UserDeactivatedBan as ea:
            await self.msg.reply_text(f"Error: Akun deactivated ban, \n{ea}")
            await self.db.delete(self.idacc, True)
            return None
        except UserDeactivated as ea:
            await self.msg.reply_text(f"Error: Akun deactivated, \n{ea}")
            await self.db.delete(self.idacc, True)
            return None
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")
            print(e)
            return None
        return []

    async def change_password(self, old_pw=None):
        db = await self.db.getConf("password")
        pw = db if db is not None else "kontolkuda"
        try:
            if old_pw is None:
                setpw = await self.np.enable_cloud_password(pw)
            else:
                setpw = await self.np.change_cloud_password(old_pw, pw)
            await self.db.updatePw(self.idacc, pw)
        except ValueError as e:
            print(e)
            return False
        except Exception as e:
            print("error", e)
            return False
        return True

    async def delete_photos(self):
        try:
            photos = [p async for p in self.np.get_chat_photos("me")]
            await self.np.delete_profile_photos([p.file_id for p in photos])
        except Exception as e:
            print(e)
            return False
        return True

    async def clearChats(self):
        try:

            async def clear_history(peer):
                delete = await self.np.invoke(
                    raw.functions.messages.delete_history.DeleteHistory(
                        peer=peer, max_id=0
                    )
                )
                if delete and delete.offset > 0:
                    await clear_history(peer)

            async for dialog in self.np.get_dialogs():
                title = dialog.chat.first_name or dialog.chat.title
                peer = await self.np.resolve_peer(dialog.chat.id)
                is_bot = dialog.chat.type == ChatType.BOT
                if isinstance(peer, InputPeerUser):
                    try:
                        # print(f"delete chat user {title}")
                        peer = await self.np.resolve_peer(dialog.chat.id)
                        if is_bot:
                            if "SpamBot" not in dialog.chat.username:
                                await self.np.block_user(dialog.chat.id)
                        # await self.np.invoke(
                        #     raw.functions.messages.delete_chat.DeleteChat(
                        #         chat_id=peer.user_id
                        #     )
                        # )
                        await clear_history(peer)
                    except FloodWait as e:
                        await self.msg.reply_text(f"FloodWait {e}")
                        await asyncio.sleep(e.value)
                    except PeerIdInvalid as e:
                        print("error", e)
                        continue
                    except Exception as e:
                        print(e)
                        continue
                else:
                    try:
                        # print(f"leave from {title}, {dialog.chat.id}")
                        # await self.np.leave_chat(dialog.chat.id, delete=True)
                        chat_id = dialog.chat.id
                        peer = await self.np.resolve_peer(chat_id)
                        if isinstance(
                                peer, raw.types.input_peer_channel.InputPeerChannel
                        ):
                            leave = await self.np.invoke(
                                raw.functions.channels.leave_channel.LeaveChannel(
                                    channel=await self.np.resolve_peer(chat_id)
                                )
                            )
                        elif isinstance(peer, raw.types.input_peer_chat.InputPeerChat):
                            r = await self.np.invoke(
                                raw.functions.messages.delete_chat_user.DeleteChatUser(
                                    chat_id=peer.chat_id,
                                    user_id=raw.types.input_user_self.InputUserSelf(),
                                    revoke_history=True,
                                )
                            )
                        await clear_history(peer)
                    except FloodWait as e:
                        await self.msg.reply_text(f"FloodWait {e}")
                        await asyncio.sleep(e.value)
                    except PeerIdInvalid as e:
                        print("error", e)
                        continue
                    except Exception as e:
                        print(e)
                        continue
        except FloodWait as e:
            await self.msg.reply_text(f"FloodWait {e.value}")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Erorr: {e}")
            return False
        return True

    async def set_profile(self, name=None, pp=None):
        try:
            await self.delete_photos()
            if pp is not None:
                await self.np.set_profile_photo(photo=pp)
            await self.np.update_profile(first_name=f"{self.idacc}", last_name="")
        except Exception as e:
            print(e)
            return False
        return True

    async def changePhone(self, idacc, newphone):
        self.new_phone = newphone
        self.phone_hash = ""
        self.phone_code = ""
        self.timeout = 180
        try:
            new_string = f"{idacc}  `{await self.np.export_session_string()}`"
            sendCodeChangePhone = await self.np.invoke(
                account.send_change_phone_code.SendChangePhoneCode(
                    phone_number=newphone,
                    settings=CodeSettings(),
                )
            )
            self.phone_hash = sendCodeChangePhone.phone_code_hash
            self.timeout = sendCodeChangePhone.timeout

            self.phone_code_msg = await self.msg.chat.ask(
                "Masukin kode OTP dengan format `1-2-3-4-5`",
                filters=filters.text,
                timeout=600,
            )
            if "/cancel" in self.phone_code_msg.text:
                await self.msg.reply_text("Kenapa dibatalin gblok")
                return
            self.phone_code = self.phone_code_msg.text.replace("-", "")

            await self.confirmChange()

        except FloodWait as flood:
            await self.msg.reply(
                f"account cannot change number because FloodWait until `{str(int(flood.value)//3600)}` hours"
            )
            return
        except PhoneNumberBanned as e:
            await self.msg.reply_text(f"Error: nomer {newphone} dibanned, {e}")
            return
        except PhoneNumberInvalid as e:
            await self.msg.reply_text(f"Error: nomer {newphone} tidak valid, {e}")
            return
        except PhoneNumberOccupied as e:
            await self.msg.reply_text(f"Error: nomer {newphone} sudah terdaftar, {e}")
            return
        except PhoneNumberFlood as e:
            await self.msg.reply_text(f"Error: nomer {newphone} flood \n{e}")
            return
        except AuthKeyUnregistered as ea:
            await self.msg.reply_text(f"Error: session telah dihapus, \n{ea}")
            return
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")
            print(e)
            return

    async def confirmChange(self):
        try:
            changePhone = await self.np.invoke(
                account.change_phone.ChangePhone(
                    phone_number=self.new_phone,
                    phone_code_hash=self.phone_hash,
                    phone_code=self.phone_code,
                )
            )
            await self.msg.reply_text(
                f"Nomer hp berhasil diganti\n{changePhone.phone}\n\n/users"
            )
            await self.db.update_safe(self.idacc, changePhone.phone)
            date_proses = await self.msg.reply_text(
                f"__Sedang mengamankan akun, pasang password,pp,nama, clear chats dulu__"
            )
            await self.proses_safe(date_proses)
            await asyncio.sleep(1)
            await self.np.stop()
        except FloodWait as flood:
            await self.msg.reply(
                f"**NUMBER** `{self.new_phone}` cannot send OTP until `{str(int(flood.value)//3600)}` hours"
            )
            return
        except AuthKeyUnregistered as ea:
            await self.msg.reply_text(f"Error: {ea}")
            await self.db.delete(self.idacc)
            return
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")
            return

    async def proses_safe(self, msg):
        datauser = await self.db.getUser(self.idacc)
        # pp = await self.db.getConf("pp")
        pp = None
        pw = datauser[4]
        try:
            await asyncio.sleep(1)
            send_pw = await msg.edit_text("__Proses ganti password__")
            gpw = await self.change_password(pw)
            await asyncio.sleep(1)
            if gpw:
                await send_pw.edit_text("__Sukses ganti password__")
            else:
                await send_pw.edit_text("__Gagal ganti password__")
            await asyncio.sleep(2)

            await send_pw.edit_text("__Update profile__")
            gpp = await self.set_profile(pp=pp)
            await asyncio.sleep(1)
            if gpp:
                await send_pw.edit_text("__Sukses update profile__")
            else:
                await send_pw.edit_text("__Gagal update profile__")
            await asyncio.sleep(2)

            await send_pw.edit_text("__Clearing chats__")
            gcc = await self.clearChats()
            await asyncio.sleep(1)
            if gcc:
                await send_pw.edit_text("__Sukses clearing chats__")
            else:
                await send_pw.edit_text("__Gagal clearing chats__")
            await asyncio.sleep(2)

            await self.np.send_message("@SpamBot", "/start")
            await self.np.send_message("@SpamBot", "/start")
            await send_pw.edit_text("__Done, akun sudah diamankan__")

        except Exception as e:
            await msg.reply_text(f"Error: {e}")
            print(e)

    async def listen(self, timeout=60):
        conf = await self.db.getConf("only_telegram")
        if conf is not None:
            if "true" in conf:
                only_tele = True
            else:
                only_tele = False
        try:
            await self.np.stop()

            @self.np.on_message()
            async def onNewMessage(client, msg):
                try:
                    usr = self.me
                    if only_tele:
                        if msg.from_user.id == 777000:
                            await self.msg.reply_text(
                                f"**FROM **@{usr.username}|`{usr.id}`(**{usr.first_name}**)\n\n{msg.text}"
                            )
                    else:
                        await self.msg.reply_text(
                            f"**FROM **@{usr.username}|`{usr.id}`(**{usr.first_name}**)\n\n{msg.text}"
                        )
                except FloodWait as e:
                    print("floadwait", e)
                    await asyncio.sleep(e.value)
                except Exception as e:
                    await self.msg.reply_text(f"Error: {e}")

            # @self.np.on_message()
            # async def onMessage(client, msg):
            #     try:
            #         await self.msg.reply_text(f"**FROM **@\n\n{msg.text}")
            #     except FloodWait as e:
            #         await self.msg.reply_text(f"FloodWait: {e}")
            #         await asyncio.sleep(e.value)
            #     except Exception as e:
            #         await self.msg.reply_text(f"Error: {e}")

            await self.np.start()
            await self.msg.reply_text(
                f"__Waiting new message__ `{self.me.id}` __from Telegram until 60 second__"
            )
            await asyncio.sleep(timeout)
            await self.np.stop()
            await self.msg.reply_text(
                f"`{self.me.id}` __Done, account has been stopped__\n/users to list again"
            )
        except AuthKeyUnregistered as ea:
            await self.msg.reply_text(f"Session dihapus oleh user, \n{ea}")
            await self.db.delete(self.idacc)
            await self.np.stop()
        except UserDeactivatedBan as ea:
            await self.msg.reply_text(f"Error: Akun deactivated ban, \n{ea}")
            await self.db.delete(self.idacc, True)
            return None
        except UserDeactivated as ea:
            await self.msg.reply_text(f"Error: Akun deactivated, \n{ea}")
            await self.db.delete(self.idacc, True)
            return None

        except FloodWait as e:
            await self.msg.reply_text(f"FloodWait: {e}")
            await asyncio.sleep(e.value)
        except Exception as e:
            await self.msg.reply_text(f"Error: {e}")
            await self.np.stop()


    async def Report(self, target):
        global getfirst
        words = ["The greatest trick scammers ever pulled was convincing the world they didn't exist.","Scammers prey on trust, turning it into their greatest weapon.","Fraud is a thief that steals not just money, but also the faith we place in one another.","Behind every scam, there's a tale of deceit and broken trust.","A scammer's promise is like a castle made of sand, destined to crumble.","Fraud: the art of deception in pursuit of ill-gotten gains.","Beware the sweet words of scammers, for they mask their true intentions.","In the realm of scams, truth becomes fiction, and fiction becomes truth.","Scammers thrive in the shadows of ignorance and misplaced trust.","Remember, a scammer's smile can hide a thousand lies.","Fraudulent","Deceptive","This scammm","Dishonest","Swindler","Charlatan","Trickster","Scammer","Scamming","Deceiver","Snake oil salesman","Sham","Cheat","Hoax","Scammers trade in illusions, preying on dreams and exploiting vulnerabilities.","Behind every successful scam, there's a trail of broken trust and shattered lives.","Fraud thrives in the absence of vigilance and the presence of greed.","Scammers are architects of deceit, constructing webs of lies to trap the unsuspecting.","In the world of scams, the only thing guaranteed is the loss of trust and financial devastation.","Fraud knows no boundaries, targeting the innocent with cunning and persistence.","Beware the allure of easy money, for it often leads to the clutches of scammers.","Scammers operate in the shadows, exploiting the vulnerability of trust for personal gain.","Fraud is a betrayal of trust, tarnishing the integrity of individuals and institutions alike.","In the battle against scams, knowledge and skepticism are our strongest shields."]
        word = random.choice(words)
        try:
            chatid = -1001757839575
            getfirst = await self.np.get_chat(target)
            if isinstance(getfirst, types.ChatPreview):
                print("preview and join")
                join = await self.np.join_chat(target)
        except ChannelInvalid:
            join = await self.np.join_chat(target)
        except Exception as e:
            print("kontol")
            await self.msg.reply_text(f"Error: {e}")
            return None
        try:
            target = await self.np.resolve_peer(chatid)
            msg = []
            async for message in self.np.get_chat_history(chat_id=chatid, limit=100):
                msg.append(message.id)
            await asyncio.sleep(5)
            report = await self.np.invoke(
                messages.report.Report(
                    peer=target,
                    id=msg,
                    reason=input_report_reason_other.InputReportReasonOther(),
                    message=word,
                )
            )
            if report:
                print(f"Reported {getfirst.title} as", word)
                await self.msg.reply_text(f"Reported {getfirst.title} as {word}")
        except Exception as e:
            e = traceback.format_exc()
            print(e)
            await self.msg.reply_text(f"Error: {e}")

    async def scrapGroup(self, target):
        try:
            if "+" in target:
                print("join first")
                target = await self.np.get_chat(target)
                asal = target.id
            elif "/joinchat/" in target:
                target = await self.np.join_chat(target)
                asal = target.id
            else:
                asal = target
            await self.np.join_chat(asal)
            channel = await self.np.resolve_peer(asal)
            getchannel = await self.np.get_chat(asal)
            member_count = getchannel.members_count
            class DataMember:
                def __init__(self, id, username):
                    self.id = id
                    self.username = username

            if isinstance(channel, input_peer_channel.InputPeerChannel):
                members = []
                limit = 200
                offset = 0
                while offset < member_count:
                    print(offset, limit)
                    participants = await self.np.invoke(
                        channels.get_participants.GetParticipants(
                            channel=channel,
                            filter=ChannelParticipantsRecent(),
                            offset=offset,
                            limit=limit,
                            hash=0,
                        )
                    )
                    print(len(participants.users))
                    for user in participants.users:
                        if user.username is not None:
                            members.append(DataMember(user.id, user.username))
                    offset += limit
                print(len(members), member_count,"channel")
                dataScrap = "members.csv"
                with open(dataScrap, "w", newline="") as csvfile:
                    fieldnames = ["id", "username"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for member in members:
                        writer.writerow(
                            {"id": member.id, "username": member.username}
                        )
            if isinstance(channel, input_peer_chat.InputPeerChat):
                print("group")
                # participants = await self.np.invoke(
                #     messages.get_full_chat.GetFullChat(chat_id=channel.chat_id)
                # )


        except Exception as e:
            e = traceback.format_exc()
            print(e)
            await self.msg.reply_text(f"Error: {e}")

    async def inviteToChannel(self, target, users):
        try:
            if "+" in target:
                await self.np.join_chat(target)
            channel = await self.np.resolve_peer(target)
            await self.np.join_chat(target)
            peer_flood = 0
            sukses = 0
            total_invite = 0
            for idx,member in enumerate(users):
                # if idx > 5:
                #     break
                try:
                    user = await self.np.resolve_peer(member)
                    print(user.user_id, member)
                    if isinstance(channel, input_peer_chat.InputPeerChat):
                        try:
                            invited = await self.np.invoke(
                                messages.add_chat_user.AddChatUser(
                                    chat_id=channel.chat_id, user_id=user, fwd_limit=42
                                )
                            )
                        except ChatIdInvalid:
                            channel = await self.np.resolve_peer(target)

                    if isinstance(channel, input_peer_channel.InputPeerChannel):
                        invited = await self.np.invoke(
                            channels.invite_to_channel.InviteToChannel(
                                channel=InputChannel(
                                    channel_id=channel.channel_id,
                                    access_hash=channel.access_hash,
                                ), users=[InputUser(
                                    user_id=user.user_id,
                                    access_hash=user.access_hash,
                                )]
                            )
                        )
                        print("invite", user.user_id,"to", channel.channel_id)
                    sukses += 1
                    total_invite += 1
                except UserAlreadyParticipant as e:
                    print(member, "UserAlreadyParticipant", e)
                    await asyncio.sleep(2)
                    continue
                except UserPrivacyRestricted as e:
                    print(member, "UserPrivacyRestricted", e)
                    await asyncio.sleep(2)
                    continue
                except UserNotMutualContact as e:
                    print(member, "UserNotMutualContact", e)
                    await asyncio.sleep(2)
                    continue
                except UserChannelsTooMuch as e:
                    print(member, "UserChannelsTooMuch", e)
                    await asyncio.sleep(2)
                    continue
                except UserKicked as e:
                    print(member, "UserKicked", e)
                    await asyncio.sleep(2)
                    continue
                except (AuthKeyUnregistered, AuthKeyDuplicated):
                    await self.np.stop()
                    break
                except PeerFlood as e:
                    peer_flood += 1
                    delay_flood = round(random.uniform(10, 15),1)
                    floodValue = e.value
                    print(member, f"PeerFlood: {e}, delay: {delay_flood}")
                    if peer_flood >= 2:
                        pass
                    else:
                        await asyncio.sleep(delay_flood)
                    continue
                except FloodWait as e:
                    print(member, "FloodWait", e)
                    await self.np.stop()
                    break
                except UserBannedInChannel as e:
                    print(member, "UserBannedInChannel", e)
                    await self.np.stop()
                    break
                except ChatAdminRequired as e:
                    print(member, "ChatAdminRequired", e)
                    await self.np.stop()
                    break
                except ChatWriteForbidden as e:
                    print(member, "ChatWriteForbidden", e)
                    await self.np.stop()
                    break
                except KeyboardInterrupt:
                    print("KeyboardInterrupt")
                    await self.np.stop()
                    break
                except Exception as e:
                    e = traceback.format_exc()
                    print(e," Exception")
                    continue
            await self.msg.reply_text(f"sukses invite {sukses} dari {total_invite}")
            return True
        except Exception as e:
            e = traceback.format_exc()
            print(e, " Exception2")
            return False

    async def stop(self):
        await self.np.stop()