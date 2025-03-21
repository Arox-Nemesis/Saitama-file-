# (©) Codeflix_Bots

import logging
import base64
import random
import re
import string
import time
import asyncio
import os 
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import (
    ADMINS,
    FORCE_MSG,
    START_MSG,
    CUSTOM_CAPTION,
    DISABLE_CHANNEL_BUTTON,
    PROTECT_CONTENT,
    OWNER_ID,
)
from helper_func import subscribed, encode, decode, get_messages, 
from database.database import add_user, del_user, full_userbase, present_user
from shortzy import Shortzy


@Bot.on_message(filters.command('start') & filters.private & subscribed & subsch1 & subsch2 & subsch3)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    owner_id = ADMINS  # Fetch the owner's ID from config

    # Check if the user is the owner
    if id == owner_id:
        await message.reply("You are the owner! Additional actions can be added here.")
    else:
        if not await present_user(id):
            try:
                await add_user(id)
            except:
                pass

    text = message.text
    if len(text) > 7:  # Indentation fixed
        try:
            base64_string = message.text.split(" ", 1)[1]
            _string = await decode(base64_string)
            argument = _string.split("-")

            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                except:
                    return

                ids = range(start, end + 1) if start <= end else []
                if start > end:
                    i = start
                    while i >= end:
                        ids.append(i)
                        i -= 1

            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except:
                    return

            temp_msg = await message.reply("Please wait...")
            try:
                messages = await get_messages(client, ids)
            except:
                await message.reply_text("Something went wrong..!")
                return

            await temp_msg.delete()
            snt_msgs = []

            for msg in messages:
                caption = (
                    CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                          filename=msg.document.file_name)
                    if bool(CUSTOM_CAPTION) and bool(msg.document)
                    else ("" if not msg.caption else msg.caption.html)
                )

                reply_markup = None if DISABLE_CHANNEL_BUTTON else msg.reply_markup

                try:
                    snt_msg = await msg.copy(
                        chat_id=message.from_user.id, 
                        caption=caption, 
                        parse_mode=ParseMode.HTML, 
                        reply_markup=reply_markup, 
                        protect_content=PROTECT_CONTENT
                    )
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    snt_msg = await msg.copy(
                        chat_id=message.from_user.id, 
                        caption=caption, 
                        parse_mode=ParseMode.HTML, 
                        reply_markup=reply_markup, 
                        protect_content=PROTECT_CONTENT
                    )
                    snt_msgs.append(snt_msg)
                except:
                    pass

            SD = await message.reply_text("Baka! Files will be deleted After 600 seconds. Save them to the Saved Message now!")
            await asyncio.sleep(600)

            for snt_msg in snt_msgs:
                try:
                    await snt_msg.delete()
                except:
                    pass

            await SD.delete()
        
        except:
            return

    await message.reply_text(
        text=START_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup([]),
        disable_web_page_preview=True,
        quote=True
    )


WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"
REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"


@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink2),
            InlineKeyboardButton(text="ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink3),
        ],
        [
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink),
        ]
    ]
    
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='• ɴᴏᴡ ᴄʟɪᴄᴋ ʜᴇʀᴇ •',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )


@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} ᴜꜱᴇʀꜱ ᴀʀᴇ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ")


@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0
        
        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴛɪʟʟ ᴡᴀɪᴛ ʙʀᴏᴏ... </i>")
        
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception as e:
                unsuccessful += 1
                logging.error(f"Broadcast Error: {e}")
            total += 1
        
        return await pls_wait.edit(f"<b><u>Broadcast Completed</u>\nTotal: {total}\nSuccess: {successful}\nBlocked: {blocked}\nDeleted: {deleted}\nFailed: {unsuccessful}</b>")

    else:
        await message.reply(REPLY_ERROR)
        
