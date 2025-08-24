import time
from telethon import events

@events.register(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    start = time.time()
    msg = await event.reply("🏓 Pong...")
    end = time.time()
    await msg.edit(f"🏓 Pong!\n⏱ {round((end - start) * 1000)} ms")
  
