from pyrogram import Client

# Apna API_ID aur API_HASH yahan daalo (jo my.telegram.org se mila tha)
api_id = 37382333         # <-- ise apne actual API_ID se replace karo
api_hash = "967aeb1c88ecf77b1a13765e79be5d60"  # <-- ise apne actual API_HASH se replace karo

print("Login karne ke liye apna PERSONAL Telegram account use karo (bot ka nahi).")
print("Ye account VC join karke gaane stream karega.\n")

with Client("assistant", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    session_string = app.export_session_string()
    print("\n=========== YE COPY KARO ===========")
    print(session_string)
    print("=====================================")
    print("\nIsko apni .env file me SESSION_STRING= ke aage paste kar do.")
