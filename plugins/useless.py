from bot import Bot
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters
from config import ADMINS, BOT_STATS_TEXT, USER_REPLY_TEXT
from datetime import datetime

@Bot.on_message(filters.command('stats') & filters.user(ADMINS))
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = str(delta).split('.')[0]  # Formats time as HH:MM:SS
    await message.reply(BOT_STATS_TEXT.format(uptime=time))

@Bot.on_message(filters.private & filters.incoming)
async def useless(_, message: Message):
    if USER_REPLY_TEXT in message.text:
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Visit Website", url="https://example.com")]
            ]
        )
        await message.reply_text(USER_REPLY_TEXT, reply_markup=keyboard)
