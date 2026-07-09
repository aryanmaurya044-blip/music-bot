# Telegram Music Bot (Pyrogram + PyTgCalls)

This bot searches YouTube for songs and plays them in a Telegram group's **Voice Chat**.

## Features
- `/play <song name or YouTube link>` — play a song / add it to the queue
- `/fplay <song name>` — **force play**: bypasses the queue and plays this song immediately (the rest of the queue shifts back, nothing is deleted). Open to all users.
- `/skip` — skip the current song *(admins/authorized/session-starter only)*
- `/pause` / `/resume` — pause/resume *(admins/authorized/session-starter only)*
- `/stop` — stop and leave the VC *(admins/authorized/session-starter only)*
- `/queue` — view the current queue
- `/auth` (reply to a user's message) — grant that user access to music-control commands
- `/unauth` (reply to a user) — revoke access

### Permission System
- Group **Telegram admins/creator** have permission by default to use `/skip`, `/pause`, `/resume`, `/stop`
- The `OWNER_ID` set in `.env` (bot owner) always has full access
- Any admin can grant regular members the same permission with `/auth`
- Whoever first starts the bot in the VC (via `/play` or `/fplay` when nothing was playing) becomes the **session owner** and can also use these controls, until the session ends (queue empties or `/stop` is used)
- `/fplay` itself has no restriction — any member can force-play a song at any time
- A non-admin/non-authorized/non-owner user trying to run a restricted command gets a "⛔ permission denied" reply

---

## Setup Steps

### 1. System dependencies
```bash
sudo apt update
sudo apt install ffmpeg -y
```

### 2. Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Get API_ID and API_HASH
- Go to https://my.telegram.org → log in → "API Development Tools" → copy your API_ID and API_HASH

### 4. Get a Bot Token
- Message **@BotFather** on Telegram with `/newbot` and copy the token

### 5. Generate an Assistant/Userbot Session String
A normal Bot account **cannot** join a Telegram Voice Chat — so a second (personal)
account is needed alongside the bot, acting as an "assistant" that joins the VC and streams.

Run a small script to generate the session string:

```python
from pyrogram import Client

api_id = 1234567       # put your API_ID here
api_hash = "your_hash" # put your API_HASH here

with Client("assistant", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    print(app.export_session_string())
```

Run this, enter your phone number/OTP, and copy the printed string into `.env` as `SESSION_STRING`.

⚠️ Never share this session string with anyone — it grants full access to that account.

### 6. Create a `.env` file
Rename `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### 7. Run the bot
```bash
python3 main.py
```

### 8. Use it in a group
1. Add the bot to a group and make it an **admin**
2. Add the assistant/userbot account to the same group
3. **Start the group's Voice Chat**
4. Send `/play tera ban jaunga` 🎶

---

## Notes
- The queue is currently in-memory (RAM) — it clears when the bot restarts. For persistence, swap `helpers/queue.py` for SQLite/MongoDB.
- Copyright: use this only for your own legitimate/personal use, and keep YouTube's Terms of Service in mind.
- If you get a `NoActiveGroupCall` error, it means the VC hasn't been started — start it first.
