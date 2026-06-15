from pathlib import Path

FILE = Path("bot.py")

# ================= YOUR CREDIT =================
YOUR_NAME = "Aɴᴋɪᴛ"
YOUR_TG_USERNAME = "AnkitShakyaX"  # @ ke bina
YOUR_CHANNEL_URL = "https://t.me/ANKIT_SHAKYA_OFFICIAL"
YOUR_CHANNEL_NAME = "𝗔𝗻𝗸𝗶𝘁 𝗦𝗵𝗮𝗸𝘆𝗮 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹"

YOUR_TG_URL = f"https://t.me/{YOUR_TG_USERNAME}"
NEW_LINK_CREDIT = f"[{YOUR_NAME}]({YOUR_TG_URL})"

# ===============================================

if not FILE.exists():
    print("❌ main.py file not found")
    exit()

data = FILE.read_text(encoding="utf-8", errors="ignore")

# Backup
backup = FILE.with_suffix(".py.bak")
backup.write_text(data, encoding="utf-8")
print(f"✅ Backup created: {backup}")

replacements = {
    # Top comments / text username
    "@Tushar0125": f"@{YOUR_TG_USERNAME}",
    "Tushar0125": YOUR_TG_USERNAME,

    # Old Telegram links
    "https://t.me/jaat_mk": YOUR_TG_URL,
    "https://t.me/inventor_king_24": YOUR_CHANNEL_URL,

    # Old names/credits
    "जाटⁱˢß𝐚𝐜𝐤ツ": YOUR_NAME,

    # Full captions
    "𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 ➤ जाटⁱˢß𝐚𝐜𝐤ツ": f"𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 ➤ {YOUR_NAME}",
    "𝗘𝗱𝗶𝘁𝗲𝗱 𝗕𝘆 ➤ जाटⁱˢß𝐚𝐜𝐤ツ": f"𝗘𝗱𝗶𝘁𝗲𝗱 𝗕𝘆 ➤ {YOUR_NAME}",
    "𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗕𝘆 ➤ जाटⁱˢß𝐚𝐜𝐤ツ": f"𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗕𝘆 ➤ {YOUR_NAME}",

    # Markdown credit link
    "[जाटⁱˢß𝐚𝐜𝐤ツ](https://t.me/jaat_mk)": NEW_LINK_CREDIT,

    # Button text
    "🇮🇳ʙᴏᴛ ᴍᴀᴅᴇ ʙʏ🇮🇳": "🇮🇳 ʙᴏᴛ ᴍᴀᴅᴇ ʙʏ 🇮🇳",
    "🔔ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ🔔": "🔔 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ 🔔",
    "🦋ғᴏʟʟᴏᴡ ᴜs🦋": "🦋 ғᴏʟʟᴏᴡ ᴜs 🦋",
}

for old, new in replacements.items():
    data = data.replace(old, new)

# Top credit force update
lines = data.splitlines()

if len(lines) >= 2:
    lines[0] = f"# Don't Remove Credit Tg - @{YOUR_TG_USERNAME}"
    lines[1] = f"# Ask Doubt on telegram @{YOUR_TG_USERNAME}"

data = "\n".join(lines) + "\n"

FILE.write_text(data, encoding="utf-8")

print("✅ Credit replaced successfully!")
print(f"👤 Name      : {YOUR_NAME}")
print(f"🔗 Telegram  : @{YOUR_TG_USERNAME}")
print(f"📢 Channel   : {YOUR_CHANNEL_NAME}")
print(f"🌐 Channel URL: {YOUR_CHANNEL_URL}")
