# (©) Codexbotz
# Recoded By @Codeflix_Bots

import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCESUB_CHANNEL, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNELS, ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

async def is_subscribed(filter, client, update):
    """Check if a user is subscribed to the required channels."""
    if not any([FORCESUB_CHANNEL, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNELS]):
        return True

    user_id = update.from_user.id
    if user_id in ADMINS:
        return True

    required_channels = [ch for ch in [FORCESUB_CHANNEL, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNELS] if ch]
    member_status = {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}

    for channel_id in required_channels:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in member_status:
                return False
        except UserNotParticipant:
            return False

    return True

async def encode(string):
    """Encode a string to Base64."""
    return base64.urlsafe_b64encode(string.encode()).decode().rstrip("=")

async def decode(base64_string):
    """Decode a Base64 string."""
    padded_string = base64_string + "=" * (-len(base64_string) % 4)
    return base64.urlsafe_b64decode(padded_string.encode()).decode()

async def get_messages(client, message_ids):
    """Retrieve messages in batches to avoid rate limits."""
    messages = []
    total_messages = 0

    while total_messages < len(message_ids):
        batch_ids = message_ids[total_messages:total_messages + 200]

        try:
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=batch_ids)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=batch_ids)
        except Exception:
            msgs = []

        total_messages += len(batch_ids)
        messages.extend(msgs)

    return messages

async def get_message_id(client, message):
    """Extract message ID from forwarded messages or Telegram links."""
    if message.forward_from_chat and message.forward_from_chat.id == client.db_channel.id:
        return message.forward_from_message_id

    if message.forward_sender_name or not message.text:
        return 0

    pattern = r"https://t.me/(?:c/)?([^/]+)/(\d+)"
    match = re.match(pattern, message.text)

    if match:
        channel_id, msg_id = match.groups()
        msg_id = int(msg_id)

        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        elif channel_id == client.db_channel.username:
            return msg_id

    return 0

subscribed = filters.create(is_subscribed)
