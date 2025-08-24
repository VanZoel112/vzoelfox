from telethon import events

@events.register(events.NewMessage(pattern=r"\.gcast (.+)"))
async def gcast(event):
    msg = event.pattern_match.group(1)
    count = 0
    async for dialog in event.client.iter_dialogs():
        try:
            await event.client.send_message(dialog.id, msg)
            count += 1
        except:
            continue
    await event.reply(f"✅ Pesan terkirim ke {count} chat")
  
