# Don't Remove Credit Tg - @Tushar0125
# Ask Doubt on telegram @Tushar0125

import os
import re
import sys
import json
import time
import m3u8
import aiohttp
import asyncio
import requests
import subprocess
import urllib.parse
from urllib.parse import urlparse, parse_qs, quote, unquote
import cloudscraper
import datetime
import random
import ffmpeg
import logging
import yt_dlp
import sqlite3
from subprocess import getstatusoutput
from aiohttp import web
from core import *
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
import yt_dlp as youtube_dl
import cloudscraper
import m3u8
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN # Import DATABASE_URL
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube

from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Import the Database class from db.py # Import db as a placeholder
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

HEALTH_PORT = int(os.getenv("PORT", 10000))

# ============================================
# HEALTH CHECK
# ============================================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler).serve_forever(), daemon=True).start()

class Database:
    def __init__(self, db_name="bot.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sudo_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_sudo_user(self, user_id: int, username: str = None):
        try:
            self.cursor.execute(
                """
                INSERT INTO sudo_users (user_id, username)
                VALUES (?, ?)
                """,
                (user_id, username)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_sudo_user(self, user_id: int):
        self.cursor.execute(
            "DELETE FROM sudo_users WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def is_sudo_user(self, user_id: int):
        self.cursor.execute(
            "SELECT user_id FROM sudo_users WHERE user_id = ?",
            (user_id,)
        )
        return self.cursor.fetchone() is not None

    def get_sudo_users(self):
        self.cursor.execute(
            """
            SELECT user_id, username, added_at
            FROM sudo_users
            ORDER BY added_at DESC
            """
        )
        return self.cursor.fetchall()


cookies_file_path = os.getenv("COOKIES_FILE_PATH", "youtube_cookies.txt")

#pwimg = "https://graph.org/file/8add8d382169e326f67e0-3bf38f92e52955e977.jpg"
#ytimg = "https://graph.org/file/3aa806c302ceec62e6264-60ced740281395f68f.jpg"
cpimg = "https://graph.org/file/5ed50675df0faf833efef-e102210eb72c1d5a17.jpg"

async def show_random_emojis(message):
    emojis = ['🎊', '🔮', '😎', '⚡️', '🚀', '✨', '💥', '🎉', '🥂', '🍾', '🦠', '🤖', '❤️‍🔥', '🕊️', '💃', '🥳','🐅','🦁']
    emoji_message = await message.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message

# Define the owner's user ID
OWNER_ID = 6748792256 # Replace with the actual owner's user ID

# Initialize the database instance globally
db = Database()


def is_owner_or_sudo(user_id: int):
    return user_id == OWNER_ID or db.is_sudo_user(user_id)

def is_authorized(user_id: int) -> bool:
    return (
        user_id == OWNER_ID
        or user_id == AUTH_CHANNEL
        or user_id in AUTH_USERS
        or db.is_sudo_user(user_id)
    )




def convert_url(url, format_type='dash'):  # Default ab DASH
    path_map = {
        'dash': 'playlists/ALLEN/x264/dash.mpd',
        'm3u8': 'playlists/ALLEN/x264/master.m3u8'
    }
    
    return re.sub(
        r'transcodedVideos/ALLEN/transcoded_video_x264_5000k_HD',
        path_map.get(format_type, path_map['dash']),
        url
    )


import re

def extract_id(url):
    patterns = [
        r'contentid=([A-Za-z0-9+/=_-]+)\.m3u8',  # .m3u8 ke pehle tak
        r'contentId=([A-Za-z0-9+/=_-]+)\.m3u8',
        r'contentHashIdl=([A-Za-z0-9+/=_-]+)\.m3u8',
        # Fallback: kuch bhi ho, contentId= ke baad se .m3u8 tak
        r'contentId=([^\.]+)\.m3u8',
        r'contentid=([^\.]+)\.m3u8',
    ]
    
    for pat in patterns:
        match = re.search(pat, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

  
# Output: U2FsdGVkX1+QnOQswJRI2Bw3dko9QWqx+vjqjCK3w+c=
def wake_player():
    try:
        requests.get("https://learnwithpw-recorded.onrender.com", timeout=10)
        time.sleep(8)
    except:
        pass
        
PLAYER_BASE = "https://learnwithpw-recorded.onrender.com/play?v="

def pw_player(url):
    decoded = urllib.parse.quote(url)

    # dash → master.m3u8
    decoded = re.sub(r'/dash/[^/]+/[0-9]+\.mp4', '/master.m3u8', decoded)

    # encode for player
    encoded = urllib.parse.quote(decoded, safe="")

    return PLAYER_BASE + encoded



async def get_signed_video_url(access_token: str, parent_id: str, child_id: str):
    if not access_token.startswith("Bearer "):
        access_token = f"Bearer {access_token}"

    headers = {
        'Host': 'api.penpencil.co',
        'Authorization': access_token,
        'Client-Id': '5eb393ee95fab7468a79d189',
        'Client-Type': 'WEB',
        'Client-Version': '200',
        'Randomid': '8ffa361e-4cc7-4948-89e8-72e552ac5460',
        'Devicetype': 'mobile',
        'Networktype': '3g',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.pw.live',
        'Referer': 'https://www.pw.live/',
        'X-Sdk-Version': '0.0.20'
    }

    signing_url = (
        f"https://api.penpencil.co/v1/videos/video-url-details"
        f"?type=BATCHES&videoContainerType=DASH&reqType=query"
        f"&childId={child_id}&parentId={parent_id}&clientVersion=201"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(signing_url, headers=headers) as response:
                if response.status == 200:
                    res_json = await response.json()
                    data_obj = res_json.get("data", {})

                    signed_url = data_obj.get("link") or data_obj.get("videoUrl") or data_obj.get("signedUrl")

                    if signed_url:
                        if signed_url.startswith("?"):
                            return signed_url
                        return signed_url
                    else:
                        return None
                else:
                    return None
        except Exception:
            return None

def extract_ids_from_url(url: str):
    """Extract parentId and childId from URL"""
    parent_id = None
    child_id = None
    
    parent_match = re.search(r'parentId=([a-f0-9]+)', url)
    if parent_match:
        parent_id = parent_match.group(1)
    
    child_match = re.search(r'childId=([a-f0-9]+)', url)
    if child_match:
        child_id = child_match.group(1)
    
    return parent_id, child_id

def clean_video_url(url: str):
    id =  url.split("/")[-2]
    url =  "https://sec-prod-mediacdn.pw.live/" + id + "/master.m3u8"

async def get_signed_m3u8_url(access_token: str, url: str):
    
    # Extract IDs from URL
    parent_id, child_id = extract_ids_from_url(url)
    
    if not parent_id or not child_id:
        return None

    # Get signed URL parameters from API
    signed_params = await get_signed_video_url(access_token, parent_id, child_id)

    if signed_params:
        # Clean the original URL first
        clean_url = clean_video_url(video_url)
        
        # If clean URL already has query params, remove everything after ?
        if '?' in clean_url:
            base_url = clean_url.split('?')[0]
        else:
            base_url = clean_url
        
        # Combine base URL with signed params
        if signed_params.startswith("?"):
            final_url = base_url + signed_params
        else:
            final_url = signed_params
        
        return final_url
    else:
        return None


bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

BOT_USERNAME = None
BOT_ID = None
BOT_NAME = None

@bot.on_message(filters.command("sudo"))
async def sudo_command(bot: Client, message: Message):
    user_id = message.from_user.id

    if user_id != OWNER_ID:
        await message.reply_text("**🚫 You are not authorized to use this command.**")
        return

    try:
        args = message.text.split()

        if len(args) < 2:
            await message.reply_text(
                "**Usage:**\n"
                "`/sudo add <user_id>`\n"
                "`/sudo remove <user_id>`\n"
                "`/sudo list`"
            )
            return

        action = args[1].lower()

        if action == "list":
            sudo_users = db.get_sudo_users()

            if not sudo_users:
                await message.reply_text("**⚠️ No sudo users found.**")
                return

            text = "**👑 Sudo Users List:**\n\n"

            for sudo_id, username, added_at in sudo_users:
                uname = f"@{username}" if username else "No username"
                text += (
                    f"**User ID:** `{sudo_id}`\n"
                    f"**Username:** {uname}\n"
                    f"**Added:** `{added_at}`\n\n"
                )

            await message.reply_text(text)
            return

        if action not in ["add", "remove"]:
            await message.reply_text(
                "**Usage:**\n"
                "`/sudo add <user_id>`\n"
                "`/sudo remove <user_id>`\n"
                "`/sudo list`"
            )
            return

        target_user_id = None
        target_username = None

        # Agar reply karke /sudo add ya /sudo remove use kiya
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username

        # Agar command me user_id diya hai
        elif len(args) >= 3:
            target_user_id = int(args[2])

        else:
            await message.reply_text(
                "**Usage:**\n"
                "`/sudo add <user_id>`\n"
                "`/sudo remove <user_id>`\n\n"
                "Ya kisi user ke message par reply karke:\n"
                "`/sudo add`\n"
                "`/sudo remove`"
            )
            return

        if action == "add":
            if target_user_id == OWNER_ID:
                await message.reply_text("**⚠️ Owner already has full access.**")
                return

            if db.add_sudo_user(target_user_id, target_username):
                await message.reply_text(
                    f"**✅ User added to sudo list.**\n\n"
                    f"**User ID:** `{target_user_id}`"
                )
            else:
                await message.reply_text(
                    f"**⚠️ User `{target_user_id}` is already in the sudo list.**"
                )

        elif action == "remove":
            if target_user_id == OWNER_ID:
                await message.reply_text("**🚫 The owner cannot be removed from the sudo list.**")
                return

            if db.remove_sudo_user(target_user_id):
                await message.reply_text(
                    f"**✅ User removed from sudo list.**\n\n"
                    f"**User ID:** `{target_user_id}`"
                )
            else:
                await message.reply_text(
                    f"**⚠️ User `{target_user_id}` is not in the sudo list.**"
                )

    except ValueError:
        await message.reply_text("**❌ Error:** Invalid user ID. Please provide a valid integer.")

    except Exception as e:
        await message.reply_text(f"**❌ Error:** `{str(e)}`")
        
# Function to check if a user is authorized
def is_authorized2(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id == AUTH_CHANNEL
    


# Sudo command to add/remove sudo users
# @bot.on_message(filters.command("sudo"))
async def sudo_command(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        await message.reply_text("**🚫 You are not authorized to use this command.**")
        return

    try:
        args = message.text.split(" ", 2)
        if len(args) < 3:
            await message.reply_text("**Usage:** `/sudo add <user_id>` or `/sudo remove <user_id>`")
            return

        action = args[1].lower()
        target_user_id = int(args[2])
        target_username = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_username = message.reply_to_message.from_user.username

        if action == "add":
            if db.add_sudo_user(target_user_id, target_username):
                await message.reply_text(f"**✅ User `{target_user_id}` added to sudo list.**")
            else:
                await message.reply_text(f"**⚠️ User `{target_user_id}` is already in the sudo list.**")
        elif action == "remove":
            if target_user_id == OWNER_ID:
                await message.reply_text("**🚫 The owner cannot be removed from the sudo list.**")
            elif db.remove_sudo_user(target_user_id):
                await message.reply_text(f"**✅ User `{target_user_id}` removed from sudo list.**")
            else:
                await message.reply_text(f"**⚠️ User `{target_user_id}` is not in the sudo list.**")
        else:
            await message.reply_text("**Usage:** `/sudo add <user_id>` or `/sudo remove <user_id>`")
    except ValueError:
        await message.reply_text("**Error:** Invalid user ID. Please provide a valid integer.")
    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")

# Inline keyboard for start command
keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🇮🇳ʙᴏᴛ ᴍᴀᴅᴇ ʙʏ🇮🇳" ,url=f"https://t.me/jaat_mk") ],
                    [
                    InlineKeyboardButton("🔔ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ🔔" ,url="https://t.me/inventor_king_24") ],
                    [
                    InlineKeyboardButton("🦋ғᴏʟʟᴏᴡ ᴜs🦋" ,url="https://t.me/inventor_king_24")
                ],
            ]
      )

# Image URLs for the random image feature
image_urls = [
    "https://files.catbox.moe/k3qs5r.jpg",
]
random_image_url = random.choice(image_urls)
caption = (
        "**ʜᴇʟʟᴏ👋**\n\n"
        "➠ **ɪ ᴀᴍ ᴛxᴛ ᴛᴏ ᴠɪᴅᴇᴏ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ.**\n"
        "➠ **ғᴏʀ ᴜsᴇ ᴍᴇ sᴇɴdf /txt.\n"
        "➠ **ғᴏʀ ɢᴜɪᴅᴇ sᴇɴᴅ /help."
)

# Start command handler
@bot.on_message(filters.command(["start"]))
async def start_command(bot: Client, message: Message):
    await bot.send_photo(chat_id=message.chat.id, photo=random_image_url, caption=caption, reply_markup=keyboard)

# Stop command handler
@bot.on_message(filters.command("stop"))
async def restart_handler(_, m: Message):
    await m.reply_text("**𝗦𝘁𝗼𝗽𝗽𝗲𝗱**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("restart"))
async def restart_handler(_, m):
    if not is_authorized(m.from_user.id):
        await m.reply_text("**🚫 You are not authorized to use this command.**")
        return
    await m.reply_text("🔮Restarted🔮", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


COOKIES_FILE_PATH = "youtube_cookies.txt"

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    if not is_authorized(m.from_user.id):
        await m.reply_text("🚫 You are not authorized to use this command.")
        return
    await m.reply_text(
        "𝗣𝗹𝗲𝗮𝘀𝗲 𝗨𝗽𝗹𝗼𝗮𝗱 𝗧𝗵𝗲 𝗖𝗼𝗼𝗸𝗶𝗲𝘀 𝗙𝗶𝗹𝗲 (.𝘁𝘅𝘁 𝗳𝗼𝗿𝗺𝗮𝘁).",
        quote=True
    )

    try:
        input_message: Message = await client.listen(m.chat.id)

        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        downloaded_path = await input_message.download()

        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        with open(COOKIES_FILE_PATH, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ 𝗖𝗼𝗼𝗸𝗶𝗲𝘀 𝗨𝗽𝗱𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆.\n\𝗻📂 𝗦𝗮𝘃𝗲𝗱 𝗜𝗻 youtube_cookies.txt."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

import tempfile

@bot.on_message(filters.command('e2t'))
async def edit_txt(client, message: Message):
    await message.reply_text(
        "🎉 **Welcome to the .txt File Editor!**\n\n"
        "Please send your `.txt` file containing subjects, links, and topics."
    )

    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.document:
        await message.reply_text("🚨 **Error**: Please upload a valid `.txt` file.")
        return

    file_name = input_message.document.file_name.lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        uploaded_file_path = os.path.join(tmpdir, file_name)

        uploaded_file = await input_message.download(uploaded_file_path)

        await message.reply_text(
            "🔄 **Send your .txt file name, or type 'd' for the default file name.**"
        )

        user_response: Message = await bot.listen(message.chat.id)
        if user_response.text:
            user_response_text = user_response.text.strip().lower()
            if user_response_text == 'd':
                final_file_name = file_name
            else:
                final_file_name = user_response_text + '.txt'
        else:
            final_file_name = file_name

        try:
            with open(uploaded_file, 'r', encoding='utf-8') as f:
                content = f.readlines()
        except Exception as e:
            await message.reply_text(f"🚨 **Error**: Unable to read the file.\n\nDetails: {e}")
            return

        subjects = {}
        current_subject = None
        for line in content:
            line = line.strip()
            if line and ":" in line:
                title, url = line.split(":", 1)
                title, url = title.strip(), url.strip()

                if title in subjects:
                    subjects[title]["links"].append(url)
                else:
                    subjects[title] = {"links": [url], "topics": []}

                current_subject = title
            elif line.startswith("-") and current_subject:
                subjects[current_subject]["topics"].append(line.strip("- ").strip())

        sorted_subjects = sorted(subjects.items())
        for title, data in sorted_subjects:
            data["topics"].sort()

        try:
            final_file_path = os.path.join(tmpdir, final_file_name)
            with open(final_file_path, 'w', encoding='utf-8') as f:
                for title, data in sorted_subjects:
                    for link in data["links"]:
                        f.write(f"{title}:{link}\n")
                    for topic in data["topics"]:
                        f.write(f"- {topic}\n")
        except Exception as e:
            await message.reply_text(f"🚨 **Error**: Unable to write the edited file.\n\nDetails: {e}")
            return

        try:
            await message.reply_document(
                document=final_file_path,
                caption="📥**𝗘𝗱𝗶𝘁𝗲𝗱 𝗕𝘆 ➤ जाटⁱˢß𝐚𝐜𝐤ツ**"
            )
        except Exception as e:
            await message.reply_text(f"🚨 **Error**: Unable to send the file.\n\nDetails: {e}")
        finally:
            pass

from pytube import Playlist
import youtube_dl

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def sanitize_filename(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

def get_videos_with_ytdlp(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result:
                title = result.get('title', 'Unknown Title')
                videos = {}
                for entry in result['entries']:
                    video_url = entry.get('url', None)
                    video_title = entry.get('title', None)
                    if video_url:
                        videos[video_title if video_title else "Unknown Title"] = video_url
                return title, videos
            return None, None
    except Exception as e:
        logging.error(f"Error retrieving videos: {e}")
        return None, None

def save_to_file(videos, name):
    filename = f"{sanitize_filename(name)}.txt"
    with open(filename, 'w', encoding='utf-8') as file:
        for title, url in videos.items():
            if title == "Unknown Title":
                file.write(f"{url}\n")
            else:
                file.write(f"{title}: {url}\n")
    return filename


@bot.on_message(filters.command('yt2txt'))
async def ytplaylist_to_txt(client: Client, message: Message):
    user_id = message.chat.id
    if user_id != OWNER_ID:
        await message.reply_text("**🚫 You are not authorized to use this command.\n\n🫠 This Command is only for owner.**")
        return

    await message.delete()
    editable = await message.reply_text("📥 **Please enter the YouTube Playlist Url :**")
    input_msg = await client.listen(editable.chat.id)
    youtube_url = input_msg.text
    await input_msg.delete()
    await editable.delete()

    title, videos = get_videos_with_ytdlp(youtube_url)
    if videos:
        file_name = save_to_file(videos, title)
        await message.reply_document(
            document=file_name,
            caption=f"`{title}`\n\n📥 𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗕𝘆 ➤ जाटⁱˢß𝐚𝗰𝗸ツ"
        )
        os.remove(file_name)
    else:
        await message.reply_text("⚠️ **Unable to retrieve videos. Please check the URL.**")


# List users command
@bot.on_message(filters.command("userlist") & filters.user(OWNER_ID))
async def list_users(client: Client, msg: Message):
    sudo_users = db.get_sudo_users()
    if sudo_users:
        users_list = "\n".join([f"User ID : `{user_id}`" for user_id in sudo_users])
        await msg.reply_text(f"SUDO_USERS :\n{users_list}")
    else:
        await msg.reply_text("No sudo users.")


# Help command
@bot.on_message(filters.command("help"))
async def help_command(client: Client, msg: Message):
    help_text = (
        "`/start` - Start the bot⚡\n\n"
        "`/txt` - Download and upload files (sudo)🎬\n\n"
        "`/restart` - Restart the bot🔮\n\n"
        "`/stop` - Stop ongoing process🛑\n\n"
        "`/cookies` - Upload cookies file🍪\n\n"
        "`/e2t` - Edit txt file📝\n\n"
        "`/yt2txt` - Create txt of yt playlist (owner)🗃️\n\n"
        "`/sudo add` - Add user or group or channel (owner)🎊\n\n"
        "`/sudo remove` - Remove user or group or channel (owner)❌\n\n"
        "`/userlist` - List of sudo user or group or channel📜\n\n"

    )
    await msg.reply_text(help_text)

# Upload command handler
@bot.on_message(filters.command(["txt"]))
async def upload(bot: Client, m: Message):
    if not is_authorized(m.chat.id):
        await m.reply_text("**🚫You are not authorized to use this bot.**")
        return

    editable = await m.reply_text(f"⚡𝗦𝗘𝗡𝗗 𝗧𝗫𝗧 𝗙𝗜𝗟𝗘⚡")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    pdf_count = 0
    img_count = 0
    zip_count = 0
    video_count = 0

    try:
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")

        links = []
        for i in content:
            if "://" in i:
                url = i.split("://", 1)[1]
                links.append(i.split("://", 1))
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif ".zip" in url:
                    zip_count += 1
                else:
                    video_count += 1
        os.remove(x)
    except:
        await m.reply_text("😶𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗶𝗹𝗲 𝗜𝗻𝗽𝘂𝘁😶")
        os.remove(x)
        return

    await editable.edit(f"`𝗧𝗼𝘁𝗮𝗹 🔗 𝗟𝗶𝗻𝗸𝘀 𝗙𝗼𝘂𝗻𝗱 𝗔𝗿𝗲 {len(links)}\n\n🔹Img : {img_count}  🔹Pdf : {pdf_count}\n🔹Zip : {zip_count}  🔹Video : {video_count}\n\n𝗦𝗲𝗻𝗱 𝗙𝗿𝗼𝗺 𝗪𝗵𝗲𝗿𝗲 𝗬𝗼𝘂 𝗪𝗮𝗻𝘁 𝗧𝗼 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱.`")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("📚 𝗘𝗻𝘁𝗲𝗿 𝗬𝗼𝘂𝗿 𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 📚\n\n🦠 𝗦𝗲𝗻𝗱 `1` 𝗙𝗼𝗿 𝗨𝘀𝗲 𝗗𝗲𝗳𝗮𝘂𝗹𝘁 🦠")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == '1':
        b_name = file_name
    else:
        b_name = raw_text0


    await editable.edit("**📸 𝗘𝗻𝘁𝗲𝗿 𝗥𝗲𝘀𝗼𝗹𝘂𝘁𝗶𝗼𝗻 📸**\n➤ `144`\n➤ `240`\n➤ `360`\n➤ `480`\n➤ `720`\n➤ `1080`")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080"
        else:
            res = "UN"
    except Exception:
            res = "UN"



    await editable.edit("📛 𝗘𝗻𝘁𝗲𝗿 𝗬𝗼𝘂𝗿 𝗡𝗮𝗺𝗲 📛\n\n🐥 𝗦𝗲𝗻𝗱 `1` 𝗙𝗼𝗿 𝗨𝘀𝗲 𝗗𝗲𝗳𝗮𝘂𝗹𝘁 🐥")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    credit = "️[जाटⁱˢß𝐚𝐜𝐤ツ](https://t.me/jaat_mk)"
    if raw_text3 == '1':
        CR = '[जाटⁱˢß𝐚𝐜𝐤ツ](https://t.me/jaat_mk)'
    elif raw_text3:
        try:
            text, link = raw_text3.split(',')
            CR = f'[{text.strip()}]({link.strip()})'
        except ValueError:
            CR = raw_text3
    else:
        CR = credit

    await editable.edit("**𝗘𝗻𝘁𝗲𝗿 𝗣𝘄 𝗧𝗼𝗸𝗲𝗻 𝗙𝗼𝗿 𝗣𝘄 𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗼𝗿 𝗦𝗲𝗻𝗱 `3` 𝗙𝗼𝗿 𝗢𝘁𝗵𝗲𝗿𝘀**")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == '3':
        MR = "token"
    else:
        MR = raw_text4



    await editable.edit("𝗡𝗼𝘄 𝗦𝗲𝗻𝗱 𝗧𝗵𝗲 𝗧𝗵𝘂𝗺𝗯 𝗨𝗿𝗹 𝗘𝗴 » https://graph.org/file/13a89d77002442255efad-989ac290c1b3f13b44.jpg\n\n𝗢𝗿 𝗜𝗳 𝗗𝗼𝗻't 𝗪𝗮𝗻𝘁 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹 𝗦𝗲𝗻𝗱 = 𝗻𝗼")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    failed_count =0
    if len(links) == 1:
        count = 1
    else:
        count = int(raw_text)

    try:
        for i in range(count - 1, len(links)):
            V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            
                

            elif "https://appx-transcoded-videos.livelearn.in/videos/rozgar-data/" in url:
                url = url.replace("https://appx-transcoded-videos.livelearn.in/videos/rozgar-data/", "")
                name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "@").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
                name = f'{str(count).zfill(3)}) {name1[:60]}'
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "https://appx-transcoded-videos-mcdn.akamai.net.in/videos/bhainskipathshala-data/" in url:
                url = url.replace("https://appx-transcoded-videos-mcdn.akamai.net.in/videos/bhainskipathshala-data/", "")
                name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "@").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
                name = f'{str(count).zfill(3)}) {name1[:60]}'
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "apps-s3-jw-prod.utkarshapp.com" in url:
                if 'enc_plain_mp4' in url:
                    url = url.replace(url.split("/")[-1], res+'.mp4')

                elif 'Key-Pair-Id' in url:
                    url = None

                elif '.m3u8' in url:
                    q = ((m3u8.loads(requests.get(url).text)).data['playlists'][1]['uri']).split("/")[0]
                    x = url.split("/")[5]
                    x = url.replace(x, "")
                    url = ((m3u8.loads(requests.get(url).text)).data['playlists'][1]['uri']).replace(q+"/", x)


            
            elif 'contentId' in url or 'master.m3u8&contentHashIdl=' in url:
                url = unquote(url)
                content = extract_id(url)
                
                encoded_content = urllib.parse.quote(content, safe="")
                
                headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': raw_text4,    
                    'accept-language': 'EN',
                    'api-version': '18',
                    'app-version': '1.4.73.2',
                    'build-number': '35',
                    'connection': 'Keep-Alive',
                    'content-type': 'application/json',
                    'device-details': 'Xiaomi_Redmi 7_SDK-32',
                    'device-id': 'c28d3cb16bbdac01',
                    'region': 'IN',
                    'user-agent': 'Mobile-Android',
                    'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                    'accept-encoding': 'gzip'
                }
                
                api_url = f"https://api.classplusapp.com/cams/uploader/video/jw-signed-url?contentId={content}"
                
                try:
                    response = requests.get(api_url, headers=headers, timeout=30)
                    response_json = response.json()
                    
                    final_url = None
                    
                    if isinstance(response_json, dict):
                        if response_json.get("url"):
                            final_url = response_json["url"]
                        elif response_json.get("drmUrls"):
                            final_url = response_json["drmUrls"].get("manifestUrl")
                        elif isinstance(response_json.get("data"), dict):
                            data = response_json["data"]
                            if data.get("url"):
                                final_url = data["url"]
                            elif data.get("drmUrls"):
                                final_url = data["drmUrls"].get("manifestUrl")
                    
                    if final_url:
                        url = final_url
                        print("\nSigned URL:\n", url)
                        print("Content ID:\n", content)
                    else:
                        print("\nFailed to get signed URL")
                        print("Response:", response_json)
                        
                except Exception as e:
                    print(f"Request Error: {e}")
            else:
                print("Invalid Link")  

            if "pw.live" in url or "sec-prod-mediacdn" in url:
             wake_player()
             url = pw_player(url)
             print("PW Player URL:", url)

            if '/master.mpd' in url:
                access_token = raw_text4
                url = await get_signed_m3u8_url(access_token, url)
                wake_player()
                url = pw_player(url)
                if url:
                    return f"✅ Succes {url}"

                return "❌ failed to get signed url"

            
            if 'content.allen.in' in url:
             url = convert_url(url, 'dash')
             fallback_url = convert_url(url, 'm3u8')
            
             print("First Change Url:", url)
             print("Fallback Change url:", fallback_url)
                
            if "/master.mpd" in url or "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
             id =  url.split("/")[-2]
             url = f"https://anonymouspwplayerr-3cfbfedeb317.herokuapp.com/pw?url={url}&token={raw_text4}"


            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'


            if 'khansirvod4.pc.cdn.bitgravity.com' in url:
               parts = url.split('/')
               part3 = parts[3]
               part4 = parts[4]
               part5 = parts[5]
               url = f"https://kgs-v4.akamaized.net/kgs-cv/{part3}/{part4}/{part5}"

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "edge.api.brightcove.com" in url:
                bcov = 'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MzUxMzUzNjIsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiYmt3cmVIWmxZMFUwVXpkSmJYUkxVemw2ZW5Oclp6MDkiLCJmaXJzdF9uYW1lIjoiY25GdVpVdG5kRzR4U25sWVNGTjRiVW94VFhaUVVUMDkiLCJlbWFpbCI6ImFFWllPRXhKYVc1NWQyTlFTazk0YmtWWWJISTNRM3BKZW1OUVdIWXJWWE0wWldFNVIzZFNLelE0ZHowPSIsInBob25lIjoiZFhSNlFrSm9XVlpCYkN0clRUWTFOR3REU3pKTVVUMDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJhVVZGZGpBMk9XSnhlbXRZWm14amF6TTBVazQxUVQwOSIsImRldmljZV90eXBlIjoid2ViIiwiZGV2aWNlX3ZlcnNpb24iOiJDaHJvbWUrMTE5IiwiZGV2aWNlX21vZGVsIjoiY2hyb21lIiwicmVtb3RlX2FkZHIiOiIyNDA5OjQwYzI6MjA1NTo5MGQ0OjYzYmM6YTNjOTozMzBiOmIxOTkifX0.Kifitj1wCe_ohkdclvUt7WGuVBsQFiz7eeXoF1RduDJi4X7egejZlLZ0GCZmEKBwQpMJLvrdbAFIRniZoeAxL4FZ-pqIoYhH3PgZU6gWzKz5pdOCWfifnIzT5b3rzhDuG7sstfNiuNk9f-HMBievswEIPUC_ElazXdZPPt1gQqP7TmVg2Hjj6-JBcG7YPSqa6CUoXNDHpjWxK_KREnjWLM7vQ6J3vF1b7z_S3_CFti167C6UK5qb_turLnOUQzWzcwEaPGB3WXO0DAri6651WF33vzuzeclrcaQcMjum8n7VQ0Cl3fqypjaWD30btHQsu5j8j3pySWUlbyPVDOk-g'
                url = url.split("bcov_auth")[0]+bcov

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "webvideos.classplusapp." in url:
               cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'

            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:
                cc = f'**➭ Index » {str(count).zfill(3)}.\n➭ Title » {name1}\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}\n**<b>━━━━━━━✦✗✦━━━━━━━</b>**'
                cyt = f'**➭ Index » {str(count).zfill(3)}.\n➭ Title » {name1}\n\n\n🔗𝗩𝗶𝗱𝗲𝗼 𝗨𝗿𝗹 ➤ <a href="{url}">__Click Here to Watch Video__</a>\n\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}**'
                cpvod = f'**➭ Index » {str(count).zfill(3)}.\n\n\n➭ Title » {name1}.({res}).mkv\n\n\n🔗𝗩𝗶𝗱𝗲𝗼 𝗨𝗿𝗹 ➤ <a href="{url}">__Click Here to Watch Video__</a>\n\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}**'
                cimg = f'**➭ Index » {str(count).zfill(3)}.\n➭ Title » {name1}\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}\n**<b>━━━━━━━✦✗✦━━━━━━━</b>**'
                cczip = f'**➭ Index » {str(count).zfill(3)}.\n➭ Title » {name1}\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}\n**<b>━━━━━━━✦✗✦━━━━━━━</b>**'
                cc1 = f'**➭ Index » {str(count).zfill(3)}.\n➭ Title » {name1}\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}\n**<b>━━━━━━━✦✗✦━━━━━━━</b>**'

                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue

                elif ".pdf" in url:
                    # ========================================================
                    # SECURE PDF BYPASS INTEGRATION (Using core.py)
                    # ========================================================
                    try:
                        await asyncio.sleep(2)
                        url = url.replace(" ", "%20")

                        # Core.py se download_secure_pdf function ko call kar rahe hain
                        downloaded_pdf = await helper.download_secure_pdf(url, name)

                        if downloaded_pdf and os.path.exists(downloaded_pdf):
                            copy = await bot.send_document(
                                chat_id=m.chat.id, 
                                document=downloaded_pdf, 
                                caption=cc1
                            )
                            count += 1
                            os.remove(downloaded_pdf)
                            print(f"[Bot Success] Successfully uploaded bypassed PDF: {downloaded_pdf}", flush=True)
                        else:
                            await m.reply_text(f"❌ Secure PDF download fail ho gaya. Link block ho chuka hai.")

                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(e.x)
                        continue
                    except Exception as e:
                        await m.reply_text(f"⚠️ PDF Download Error: {str(e)}")

                elif "media-cdn.classplusapp.com/drm/" in url:
                    try:
                        await bot.send_photo(chat_id=m.chat.id, photo=cpimg, caption=cpvod)
                        count +=1
                    except Exception as e:
                        await m.reply_text(str(e))
                        time.sleep(1)
                        continue


                elif any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png"]):
                    try:
                        await asyncio.sleep(4)
                        url = url.replace(" ", "%20")

                        scraper = cloudscraper.create_scraper()
                        response = scraper.get(url)

                        if response.status_code == 200:
                            with open(f'{name}.jpg', 'wb') as file:
                                file.write(response.content)

                            await asyncio.sleep(2)
                            copy = await bot.send_photo(chat_id=m.chat.id, photo=f'{name}.jpg', caption=cimg)
                            count += 1
                            os.remove(f'{name}.jpg')

                        else:
                            await m.reply_text(f"Failed to download Image: {response.status_code} {response.reason}")

                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(2)
                        return
                    except Exception as e:
                        await m.reply_text(f"An error occurred: {str(e)}")
                        await asyncio.sleep(4)

                elif ".zip" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.zip" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.zip', caption=cczip)
                        count += 1
                        os.remove(f'{name}.zip')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                else:
                    emoji_message = await show_random_emojis(message)
                    remaining_links = len(links) - count
                    Show = f"**🍁 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗𝗜𝗡𝗚 🍁**\n\n**📝ɴᴀᴍᴇ » ** `{name}\n\n🔗ᴛᴏᴛᴀʟ ᴜʀʟ » {len(links)}\n\n🗂️ɪɴᴅᴇ𝘅 » {str(count)}/{len(links)}\n\n🌐ʀᴇᴍᴀɪɴɪŋ ᴜʀʟ » {remaining_links}\n\n❄ǫᴜᴀʟɪᴛʏ » {res}`\n\n**🔗ᴜʀʟ » ** `{url}`\n\n**🎯 Bypass Mode Active (m3u8 check)**\n\n𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 ➤ जाटⁱˢß𝐚𝐜𝐤ツ\n\n"
                    prog = await m.reply_text(Show)
                    
                    # ========================================================
                    # SECURE VIDEO STREAM BYPASS INTEGRATION (Using core.py)
                    # ========================================================
                    # Check karna ki video secure m3u8 playlist stream hai ya normal
                    is_secure_stream = "transcoded-videos.classx.co.in" in url.lower() or "classx.co.in" in url.lower()
                    
                    if is_secure_stream:
                        print(f"[Bot Router] Routing to helper.download_secure_video for URL: {url}", flush=True)
                        res_file = await helper.download_secure_video(url, name)
                    else:
                        print(f"[Bot Router] Routing to standard helper.download_video for URL: {url}", flush=True)
                        res_file = await helper.download_video(url, cmd, name)
                    
                    # Process success response
                    if res_file and os.path.exists(res_file):
                        filename = res_file
                        await prog.delete(True)
                        await emoji_message.delete()
                        await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                        count += 1
                        time.sleep(1)
                    else:
                        await prog.delete(True)
                        await emoji_message.delete()
                        await m.reply_text(f"❌ **Downloading Failed!** Link validation blocked or expired.")
                        count += 1
                        failed_count += 1

            except Exception as e:
                if "youtube.com" in url or "youtu.be" in url:
                    await m.reply_text(f"➭ Index » {str(count).zfill(3)}.\n"
                                       f"➭ Title » {name1}\n"
                                       f"➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n\n"
                                       f"YouTube : CLICK HERE({url})")
                else:
                    await m.reply_text(f'‼️𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗙𝗮𝗶𝗹𝗲𝗱‼️\n\n'
                                       f'📝𝗡𝗮𝗺𝗲 » `{name}`\n\n'
                                       f'🔗𝗨𝗿𝗹 » <a href="{url}">__**Click Here to See Link**__</a>`')

                count += 1
                failed_count += 1
                continue


    except Exception as e:
        await m.reply_text(e)
    await m.reply_text(f"`✨𝗕𝗔𝗧𝗖𝗛 𝗦𝗨𝗠𝗠𝗔𝗥𝗬✨\n\n"
                       f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                       f"📛𝗜𝗻𝗱𝗲𝘅 𝗥𝗮𝗻𝗴𝗲 » ({raw_text} to {len(links)})\n"
                       f"📚𝗕𝗮𝘁𝗰𝐡 𝗡𝗮𝗺𝗲 » {b_name}\n\n"
                       f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                       f"✨𝗧𝗫𝗧 𝗦𝗨𝗠𝗠𝗔𝗥𝗬✨ : {len(links)}\n"
                       f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                       f"🔹𝗩𝗶𝗱𝗲𝗼 » {video_count}\n🔹𝗣𝗱𝗳 » {pdf_count}\n🔹𝗜𝗺𝗴 » {img_count}\n🔹𝗭𝗶𝗽 » {zip_count}\n🔹𝗙𝗮𝗶𝗹𝗲𝗱 𝗨𝗿𝗹 » {failed_count}\n\n"
                       f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                       f"✅𝗦𝗧𝗔𝗧𝗨𝗦 » 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗`")
    await m.reply_text(f"<pre><code>📥𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗕𝘆 ➤『{CR}』</code></pre>")
    await m.reply_text(f"<pre><code>『😏𝗥𝗲𝗮𝗰𝘁𝗶𝗼н 𝗞𝗼𝗻 𝗗𝗲𝗴𝗮😏』</code></pre>")



async def fetch_bot_info():
    global BOT_USERNAME, BOT_ID, BOT_NAME

    me = await bot.get_me()

    BOT_USERNAME = me.username
    BOT_ID = me.id
    BOT_NAME = me.first_name

    print("================================", flush=True)
    print(f"🤖 Bot Name     : {BOT_NAME}", flush=True)
    print(f"🔗 Bot Username : @{BOT_USERNAME}", flush=True)
    print(f"🆔 Bot ID       : {BOT_ID}", flush=True)
    print("================================", flush=True)


async def main():
    await bot.start()
    await fetch_bot_info()
    print("✅ Bot started successfully!", flush=True)
    await idle()
    await bot.stop()


bot.run(main())
