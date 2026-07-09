"""
Simple in-memory queue manager.
Each chat_id maps to a list of songs.
For production, move this to SQLite/MongoDB so the queue survives bot restarts.
"""

queues = {}  # {chat_id: [ {"title": str, "path": str, "requested_by": str}, ... ]}


def add_to_queue(chat_id: int, song: dict):
    queues.setdefault(chat_id, [])
    queues[chat_id].append(song)


def insert_now_playing(chat_id: int, song: dict):
    """
    For force-play: replaces the current song by inserting this one
    at index 0. The rest of the existing queue stays in order behind it.
    """
    queues.setdefault(chat_id, [])
    queues[chat_id].insert(0, song)


def get_queue(chat_id: int):
    return queues.get(chat_id, [])


def pop_next(chat_id: int):
    """Removes the current song and returns the next one (front of queue)."""
    if chat_id in queues and queues[chat_id]:
        queues[chat_id].pop(0)
    return queues.get(chat_id, [None])[0] if queues.get(chat_id) else None


def clear_queue(chat_id: int):
    queues[chat_id] = []


def is_queue_empty(chat_id: int) -> bool:
    return not queues.get(chat_id)
