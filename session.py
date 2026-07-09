"""
Tracks which user started the VC session in a given chat
(i.e. the first time the bot joins the VC with an empty queue).
This "session owner" can also use skip/pause/resume/stop,
in addition to group admins/authorized users.
"""

session_owner = {}  # {chat_id: user_id}


def set_owner(chat_id: int, user_id: int):
    session_owner[chat_id] = user_id


def get_owner(chat_id: int):
    return session_owner.get(chat_id)


def is_owner(chat_id: int, user_id: int) -> bool:
    return session_owner.get(chat_id) == user_id


def clear_owner(chat_id: int):
    session_owner.pop(chat_id, None)
