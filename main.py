import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING
from helpers.downloader import search_and_download
from helpers import queue as q
from helpers import session
from helpers.auth import require_permission, add_authorized, remove_authorized

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT (Python 3.13 fix):
# We explicitly create the event loop *before* creating any Client/PyTgCalls
# objects, and set it as the current loop. Pyrogram's Client grabs "the
# current event loop" as soon as it's constructed. If we let asyncio.run()
# create its own loop later, it won't match the loop the clients grabbed at
# import time, causing "Task ... attached to a different loop" errors.
# By creating the loop first and running everything on that same loop
# (via loop.run_until_complete instead of asyncio.run), everything stays
# consistent.
# ---------------------------------------------------------------------------
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ---- Two clients are needed ----
# 1) bot_app  -> the normal bot that listens for commands (@BotFather token)
# 2) user_app -> assistant/userbot account that actually joins the VC and streams
bot_app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# PyTgCalls also gets created on this same loop, but lazily inside main()
# (after the clients are started), which is the safest point to create it.
call_py: PyTgCalls = None


async def play_next(chat_id: int):
    """Picks the next song from the queue and streams it."""
    if q.is_queue_empty(chat_id):
        await call_py.leave_call(chat_id)
        session.clear_owner(chat_id)
        return

    song = q.get_queue(chat_id)[0]
    await call_py.play(chat_id, MediaStream(song["path"]))
    await bot_app.send_message(chat_id, f"▶️ Now playing: **{song['title']}**")


@bot_app.on_message(filters.command("play") & filters.group)
async def play_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/play song name or YouTube link`")
        return

    query = message.text.split(None, 1)[1]
    status_msg = await message.reply_text(f"🔎 Searching for: **{query}**...")

    try:
        song = await asyncio.to_thread(search_and_download, query)
    except Exception as e:
        await status_msg.edit_text(f"❌ Could not find the song: `{e}`")
        return

    song["requested_by"] = message.from_user.mention
    chat_id = message.chat.id
    q.add_to_queue(chat_id, song)

    # If something is already streaming, just add this to the queue
    if len(q.get_queue(chat_id)) > 1:
        await status_msg.edit_text(f"✅ Added to queue: **{song['title']}**")
        return

    try:
        await call_py.play(chat_id, MediaStream(song["path"]))
        session.set_owner(chat_id, message.from_user.id)  # this user started the bot, so they control it
        await status_msg.edit_text(f"▶️ Now playing: **{song['title']}**")
    except NoActiveGroupCall:
        await status_msg.edit_text("⚠️ Start the group's Voice Chat first, then use /play.")
        q.clear_queue(chat_id)


@bot_app.on_message(filters.command(["fplay", "forceplay"]) & filters.group)
async def force_play_cmd(client: Client, message: Message):
    # This command is open to all users, no permission check

    if len(message.command) < 2:
        await message.reply_text("Usage: `/fplay song name or YouTube link`")
        return

    query = message.text.split(None, 1)[1]
    chat_id = message.chat.id
    status_msg = await message.reply_text(f"⚡ Force-playing: **{query}**...")

    try:
        song = await asyncio.to_thread(search_and_download, query)
    except Exception as e:
        await status_msg.edit_text(f"❌ Could not find the song: `{e}`")
        return

    song["requested_by"] = message.from_user.mention

    # If there was no active session/queue before this, this user is the one
    # "starting" the bot -- so make them the session owner
    is_fresh_session = q.is_queue_empty(chat_id)

    # Keep the existing queue intact, just insert this song at position #0
    # (it becomes the new "currently playing" track, the rest shift back)
    q.insert_now_playing(chat_id, song)

    try:
        # Calling play() immediately replaces whatever was streaming before
        await call_py.play(chat_id, MediaStream(song["path"]))
        if is_fresh_session:
            session.set_owner(chat_id, message.from_user.id)
        await status_msg.edit_text(f"⚡ Force-play: **{song['title']}** is now playing!")
    except NoActiveGroupCall:
        await status_msg.edit_text("⚠️ Start the group's Voice Chat first, then use /fplay.")
        q.pop_next(chat_id)  # remove the song we just inserted


@bot_app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(client: Client, message: Message):
    if not await require_permission(client, message):
        return

    chat_id = message.chat.id
    if q.is_queue_empty(chat_id):
        await message.reply_text("The queue is empty.")
        return

    q.pop_next(chat_id)
    if q.is_queue_empty(chat_id):
        await call_py.leave_call(chat_id)
        session.clear_owner(chat_id)
        await message.reply_text("⏭ Skipped. Queue is now empty, left the VC.")
    else:
        await play_next(chat_id)
        await message.reply_text("⏭ Skipped.")


@bot_app.on_message(filters.command("pause") & filters.group)
async def pause_cmd(client: Client, message: Message):
    if not await require_permission(client, message):
        return
    await call_py.pause(message.chat.id)
    await message.reply_text("⏸ Paused.")


@bot_app.on_message(filters.command("resume") & filters.group)
async def resume_cmd(client: Client, message: Message):
    if not await require_permission(client, message):
        return
    await call_py.resume(message.chat.id)
    await message.reply_text("▶️ Resumed.")


@bot_app.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client: Client, message: Message):
    if not await require_permission(client, message):
        return
    chat_id = message.chat.id
    q.clear_queue(chat_id)
    session.clear_owner(chat_id)
    await call_py.leave_call(chat_id)
    await message.reply_text("⏹ Stopped and cleared the queue.")


@bot_app.on_message(filters.command("queue") & filters.group)
async def queue_cmd(client: Client, message: Message):
    songs = q.get_queue(message.chat.id)
    if not songs:
        await message.reply_text("The queue is empty.")
        return

    text = "🎶 **Current Queue:**\n\n"
    for i, s in enumerate(songs, start=1):
        text += f"{i}. {s['title']} — requested by {s['requested_by']}\n"
    await message.reply_text(text)


@bot_app.on_message(filters.command("auth") & filters.group)
async def auth_cmd(client: Client, message: Message):
    # Only group admins/owner can add new authorized users
    if not await require_permission(client, message):
        return

    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2 and message.command[1].isdigit():
        target = await client.get_users(int(message.command[1]))

    if not target:
        await message.reply_text(
            "Who should be authorized? Reply to their message with `/auth`, "
            "or send `/auth <user_id>`."
        )
        return

    add_authorized(message.chat.id, target.id)
    await message.reply_text(f"✅ {target.mention} can now use music commands in this group.")


@bot_app.on_message(filters.command("unauth") & filters.group)
async def unauth_cmd(client: Client, message: Message):
    if not await require_permission(client, message):
        return

    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) >= 2 and message.command[1].isdigit():
        target = await client.get_users(int(message.command[1]))

    if not target:
        await message.reply_text(
            "Who should be unauthorized? Reply to their message with `/unauth`."
        )
        return

    remove_authorized(message.chat.id, target.id)
    await message.reply_text(f"🚫 {target.mention}'s authorization has been removed.")


@bot_app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 Hi! Make me an admin in a group, start the Voice Chat, then send\n"
        "`/play <song name>` and I'll start playing music.\n\n"
        "**Commands:**\n"
        "`/play` — play a song / add it to the queue\n"
        "`/fplay` — force-play instantly (open to all users)\n"
        "`/skip /pause /resume /stop` — admins/authorized/session-starter only*\n"
        "`/queue` — view the current queue\n"
        "`/auth` (reply to a user) — grant them command access\n"
        "`/unauth` (reply to a user) — revoke access\n\n"
        "*Whoever first starts the bot in the VC (via /play or /fplay) can also "
        "use the other controls, in addition to admins, until the session ends."
    )


def register_stream_end_handler():
    """
    Different py-tgcalls versions expose the "song finished" event under
    different names/APIs. Try the known ones so the bot keeps working
    across versions. If none are found, auto-advancing the queue is
    disabled, but /play, /fplay, /skip, /stop etc. still work normally --
    you'd just need to run /skip manually when a song ends.
    """
    if hasattr(call_py, "on_stream_end"):
        @call_py.on_stream_end()
        async def _on_stream_end(client, update):
            chat_id = update.chat_id
            q.pop_next(chat_id)
            await play_next(chat_id)
        logger.info("Registered on_stream_end handler (legacy API).")
        return

    if hasattr(call_py, "on_update"):
        @call_py.on_update()
        async def _on_update(client, update):
            # Only react to updates that look like a "stream ended" event
            if "streamend" in type(update).__name__.lower():
                chat_id = getattr(update, "chat_id", None)
                if chat_id is not None:
                    q.pop_next(chat_id)
                    await play_next(chat_id)
        logger.info("Registered on_update handler for stream-end events (new API).")
        return

    logger.warning(
        "Could not find a stream-end event handler on this py-tgcalls version. "
        "Auto-advancing the queue is disabled -- use /skip manually when a song ends."
    )


async def main():
    global call_py
    await user_app.start()
    logger.info("Assistant/userbot account started.")
    await bot_app.start()
    logger.info("Bot account started.")
    call_py = PyTgCalls(user_app)
    await call_py.start()
    register_stream_end_handler()
    logger.info("Bot and assistant are both up. Music bot is ready!")
    await asyncio.Event().wait()  # keep running forever


if __name__ == "__main__":
    loop.run_until_complete(main())
