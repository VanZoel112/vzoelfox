from telethon import events
from config import SESSION

@events.register(events.NewMessage(pattern=r"\.alive"))
async def alive(event):
    await event.reply(
        f"⚡ **Vzoel Assistant Aktif** ⚡\n"
        f"💎 Session: `{SESSION}`\n"
        f"🔥 Dibuat khusus untuk Master"
    )
  
