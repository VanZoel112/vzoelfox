from telethon import events

COMMANDS = {
    ".alive": "Cek status bot",
    ".ping": "Cek kecepatan respon",
    ".gcast <pesan>": "Broadcast pesan ke semua chat",
    ".emoji <kategori>": "Kirim kumpulan emoji (love, fire, star, dst)",
    ".joinvc": "Join voice chat grup",
    ".leavevc": "Keluar dari voice chat",
    ".id": "Lihat ID user/chat",
    ".help": "Tampilkan daftar command"
}

@events.register(events.NewMessage(pattern=r"\.help"))
async def help_cmd(event):
    text = "**📜 Vzoel Assistant Command List 📜**\n\n"
    for cmd, desc in COMMANDS.items():
        text += f"• `{cmd}` → {desc}\n"
    await event.reply(text)
  
