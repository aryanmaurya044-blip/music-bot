"""
Permission system:
- Group Telegram admins/creator have permission by default
- OWNER_ID (bot owner) always has permission
- Extra users can be authorized per-group via the /auth command
- The user who started the current VC session (via /play or /fplay) also
  has permission until the session ends
"""

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from config import OWNER_ID
from helpers import session

# {chat_id: {user_id, user_id, ...}}
authorized_users = {}


def add_authorized(chat_id: int, user_id: int):
    authorized_users.setdefault(chat_id, set())
    authorized_users[chat_id].add(user_id)


def remove_authorized(chat_id: int, user_id: int):
    if chat_id in authorized_users:
        authorized_users[chat_id].discard(user_id)


def is_manually_authorized(chat_id: int, user_id: int) -> bool:
    return user_id in authorized_users.get(chat_id, set())


async def is_admin_or_authorized(client: Client, message: Message) -> bool:
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Always allow the bot owner
    if user_id == OWNER_ID:
        return True

    # Check the manually authorized list
    if is_manually_authorized(chat_id, user_id):
        return True

    # The user who started the current session is also allowed
    if session.is_owner(chat_id, user_id):
        return True

    # Check whether the user is a group admin/creator
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def require_permission(client: Client, message: Message) -> bool:
    """
    Returns True if the user has permission.
    If not, it replies on its own and returns False.
    """
    allowed = await is_admin_or_authorized(client, message)
    if not allowed:
        await message.reply_text(
            "⛔ This command can only be used by group **admins**, **authorized users**, "
            "or whoever started the current session."
        )
    return allowed
