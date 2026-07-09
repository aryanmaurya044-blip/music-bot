import os
from dotenv import load_dotenv

load_dotenv()

# Get these from my.telegram.org
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# Get this from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Session string of the assistant/userbot account
# (this account joins the VC and streams, since a normal Bot account can't join a VC)
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Telegram user ID of the bot owner (for admin-level commands)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

DOWNLOADS_DIR = "downloads"
