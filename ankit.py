import re
import os
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
from converter import download_html
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
AUTH_CHANNEL = -1003884699177
AUTH_USERS = [8085418235,8348202390,8295147093,5817712634,8308048375,6748792256,8112779349,7967804634,8450755369,5576374587]

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




import re
def extract_ids_from_url(url: str):
    parent_id = None
    child_id = None
    
    parent_match = re.search(r'parentId=([a-f0-9]+)', url)
    if parent_match:
        parent_id = parent_match.group(1)
        print(f"Found parentId: {parent_id}")
    
    child_match = re.search(r'childId=([a-f0-9]+)', url)
    if child_match:
        child_id = child_match.group(1)
        print(f"Found childId: {child_id}")
    
    if not parent_id or not child_id:
        print("Failed to extract IDs from URL")
    
    return parent_id, child_id
    
def clean_video_url(url):
    path = urlparse(url).path
    video_id = path.split("/")[-2]
    return f"https://sec-prod-mediacdn.pw.live/{video_id}/master.m3u8"




def pw_player2(url):
    if not url:
        return None

    return PLAYER_BASE + urllib.parse.quote(str(url), safe="")

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

def extract_ids_from_url2(url: str):
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

def clean_video_url2(url: str):
    id_vid =  url.split("/")[-2]
    url =  "https://sec-prod-mediacdn.pw.live/{id_vid}/master.m3u8"

async def get_signed_m3u8_url(access_token: str, url: str):
    
    # Extract IDs from URL
    parent_id, child_id = extract_ids_from_url2(url)
    
    if not parent_id or not child_id:
        return None

    # Get signed URL parameters from API
    signed_params = await get_signed_video_url(access_token, parent_id, child_id)

    if signed_params:
        # Clean the original URL first
        clean_url = clean_video_url(url)
        
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


def try_decrypt_pdf(encrypted_path, output_path, key_str):
    """
    Standard AES-128-CBC Decryption PDF file ke liye openssl module ka use karke.
    """
    if not key_str:
        # Agar key nahi hai toh check karein ki kya ye already valid PDF hai
        with open(encrypted_path, 'rb') as f:
            if f.read(4) == b'%PDF':
                shutil.copy(encrypted_path, output_path)
                return True
        return False

    print(f"[Decrypt PDF] Decrypting file with key: {key_str}", flush=True)
    
    with open(encrypted_path, 'rb') as f:
        file_data = f.read()

    if len(file_data) < 32:
        return False

    iv_bytes = file_data[:16]
    ciphertext_bytes = file_data[16:]

    # Temp files created
    temp_cipher = f"temp_cipher_{os.getpid()}.bin"
    temp_plain = f"temp_plain_{os.getpid()}.pdf"

    with open(temp_cipher, "wb") as f:
        f.write(ciphertext_bytes)

    hex_iv = iv_bytes.hex()

    # MD5, SHA-256 aur plain string padding ko try karne ke liye list
    candidates = [
        key_str.encode('utf-8')[:16].ljust(16, b'\x00'), # Plain padded key
        hashlib.md5(key_str.encode('utf-8')).digest(),   # MD5 Key
        hashlib.sha256(key_str.encode('utf-8')).digest()[:16] # SHA-256 Key
    ]

    for cand_bytes in candidates:
        hex_key = cand_bytes.hex()
        
        # Method 1: IV block parsing decryption
        cmd = [
            "openssl", "aes-128-cbc", "-d",
            "-K", hex_key,
            "-iv", hex_iv,
            "-in", temp_cipher,
            "-out", temp_plain
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if os.path.exists(temp_plain):
            with open(temp_plain, "rb") as check_f:
                if check_f.read(4) == b'%PDF':
                    print("[Decrypt PDF] Success! Valid PDF header matched.", flush=True)
                    shutil.move(temp_plain, output_path)
                    if os.path.exists(temp_cipher): os.remove(temp_cipher)
                    return True
            os.remove(temp_plain)

        # Method 2: Zero IV decryption (Pure file layout)
        cmd_zero = [
            "openssl", "aes-128-cbc", "-d",
            "-K", hex_key,
            "-iv", "00000000000000000000000000000000",
            "-in", encrypted_path,
            "-out", temp_plain
        ]
        subprocess.run(cmd_zero, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if os.path.exists(temp_plain):
            with open(temp_plain, "rb") as check_f:
                if check_f.read(4) == b'%PDF':
                    print("[Decrypt PDF] Success with Zero-IV padding!", flush=True)
                    shutil.move(temp_plain, output_path)
                    if os.path.exists(temp_cipher): os.remove(temp_cipher)
                    return True
            os.remove(temp_plain)

    if os.path.exists(temp_cipher): os.remove(temp_cipher)
    return False

async def encrypted_pdf(url, name, enc_key):
    clean_name = f"{name}.pdf" if not name.endswith(".pdf") else name
    temp_enc = f"temp_enc_{os.getpid()}.pdf"
    print(f"[Secure PDF] Appx bypass download started for: {clean_name}", flush=True)
    
    cmd = [
        "curl", "-L",
        "-H", "User-Agent: Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "-H", "Referer: https://appx-play.akamai.net.in/",
        "-o", temp_enc,
        url
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode == 0 and os.path.exists(temp_enc):
            # PDF decrypt karne ki koshish karein
            decrypted = try_decrypt_pdf(temp_enc, clean_name, enc_key)
            if decrypted and os.path.exists(clean_name):
                if os.path.exists(temp_enc): os.remove(temp_enc)
                return clean_name
            else:
                # Agar decrypt nahi ho paya fir bhi original copy safe rakhna
                with open(temp_enc, 'rb') as f:
                    if f.read(4) == b'%PDF':
                        shutil.move(temp_enc, clean_name)
                        return clean_name
                print("[Secure PDF] Error: PDF is corrupted or has un-matching encryption key.", flush=True)
                if os.path.exists(temp_enc): os.remove(temp_enc)
                return None
        else:
            print("[Secure PDF] Error: curl download process failed.", flush=True)
            if os.path.exists(temp_enc): os.remove(temp_enc)
            return None
    except Exception as e:
        print(f"[Secure PDF] Exception: {str(e)}", flush=True)
        if os.path.exists(temp_enc): os.remove(temp_enc)
        return None
        

# ==================== API CONFIGURATION ====================
API_URL = "http://192.0.0.4:5000"  # Replace with your Flask server IP

def get_api_extension(url):
    url_lower = url.lower()
    if ".ws" in url_lower:
        return ".html"
    elif ".pdf" in url_lower:
        return ".pdf"
    elif ".mp4" in url_lower or ".m3u8" in url_lower:
        return ".mp4"
    else:
        return ".bin"

async def get_signed_videourl(url, access_token):
    vid_id =  url.split("/")[-2]
    parent_id = url.split("parentId=")[1].split("&")[0]
    child_id = url.split("childId=")[1]
    print(f"Parent ID: {parent_id}")
    print(f"Child ID: {child_id}")
    if "d1d34p8vz63oiq.cloudfront.net" in url:
        url = url.replace("d1d34p8vz63oiq.cloudfront.net", "sec-prod-mediacdn.pw.live")
        
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
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko)',
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
                        # FIX: Agar API response sirf '?URLPrefix' se shuru ho raha hai
                        if signed_url.startswith("?"):
                            
                            # Original input URL se base structure extract karna
                            # E.g., https://.../5830febe-af45-446b-939b-5434194d3305/master.mpd
                            clean_base = url.split("?")[0].split("&")[0]
                            
                            if "master.mpd" in clean_base:
                                clean_base = clean_base.replace("master.mpd", "master.m3u8")

                            signed_url = clean_base + signed_url
                        return signed_url
                    else:
                        print("❌ Response pass par data payload empty mila.")
                        return None
                else:
                    print(f"❌ Server Error: Status Code {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Connection Request Failed: {e}")
            return None

def extract_ids_urlparse(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    parent_id = params.get('parentId', [None])[0]
    child_id = params.get('childId', [None])[0]
    
    return parent_id, child_id


async def get_final_player_url(session: aiohttp.ClientSession, url, access_token: str) -> str:
    vid_id =  url.split("/")[-2]
    parent_id = url.split("parentId=")[1].split("&")[0]
    child_id = url.split("childId=")[1]
    print(f"Parent ID: {parent_id}")
    print(f"Child ID: {child_id}")
    # Authorization header normalization validation
    
    headers = {
        'Host': 'api.penpencil.co',
        'Authorization': access_token,
        'Client-Id': '5eb393ee95fab7468a79d189',
        'Client-Type': 'WEB',
        'Client-Version': '1.0.0',
        'Content-Type': 'application/json',
        'Origin': 'https://www.pw.live',
        'Referer': 'https://www.pw.live/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
    }
    
    api_url = (
        f"https://api.penpencil.co/v1/videos/video-url-details"
        f"?type=BATCHES&videoContainerType=DASH&reqType=query"
        f"&childId={child_id}&parentId={parent_id}&clientVersion=201"
    )
    
    try:
        # Step 1: Secure options handshake mechanism trigger execution
        async with session.options(api_url, headers=headers):
            pass
            
        # Step 2: Request final signing payload token suffix matrix
        async with session.get(api_url, headers=headers) as response:
            if response.status == 200:
                res_json = await response.json()
                token_suffix = res_json.get("data", {}).get("link") or res_json.get("data", {}).get("videoUrl")
                
                if token_suffix and "URLPrefix=" in token_suffix:
                    # Query suffix slicing formatting boundary constraints safely
                    query_part = token_suffix if token_suffix.startswith("?") else f"?{token_suffix.split('?')[1]}"
                    
                    # Regex scanning matching properties safely
                    expires = re.search(r'Expires=([^&]+)', query_part).group(1)
                    key_name = re.search(r'KeyName=([^&]+)', query_part).group(1)
                    signature = re.search(r'Signature=([^&]+)', query_part).group(1)
                    url_prefix = re.search(r'URLPrefix=([^&]+)', query_part).group(1)
                    
                    # Step 3: Domain Swap + Extension Format Swap Routing Matrix (.m3u8)
                    signed_m3u8 = (
                        f"https://sec-prod-mediacdn.pw.live/{vid_id}/master.m3u8"
                        f"?URLPrefix={url_prefix}&Expires={expires}&KeyName={key_name}&Signature={signature}"
                    )
                    
                    # Step 4: Double Web Safe Encoding layer calculation conversion matrix
                    first_encode = quote(signed_m3u8, safe='')
                    double_encoded_url = quote(first_encode, safe='')
                    
                    # Step 5: Final output concatenation merge framework integration
                    final_player_url = f"https://learnwithpw-recorded.onrender.com/play?v={first_encoded}"
                    return final_player_url
                    
    except Exception as e:
        logging.error(f"Error executing core signed token payload calculation: {e}")
        
    return ""
    

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

async def get_credit_name(bot, m, editable, user_id, user_first_name, user_username, user_mention):
    """Helper function to get credit name from user"""
    
    owner_credit = f"𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚™🇮🇳"
    
    credit_options = (
        f"**Choose your credit name:**\n\n"
        f"👤 **Your Name:** {user_mention}\n"
        f"🔖 **Username:** @{user_username if user_username else 'Not set'}\n\n"
        f"**Options:**\n"
        f"• Send `de` - Use bot owner's name\n"
        f"• Send `me` - Use your Telegram name\n"
        f"• Send `username` - Use your @username\n"
        f"• Or type any custom name\n\n"
        f"**Default:** Owner's credit"
    )
    
    await editable.edit(credit_options)
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    
    # Process selection
    if raw_text3 == 'de':
        CR = owner_credit
        credit_display = "Bot Owner"
    elif raw_text3 == 'me':
        CR = user_mention
        credit_display = user_first_name
    elif raw_text3 == 'username':
        if user_username:
            CR = f"@{user_username}"
            credit_display = f"@{user_username}"
        else:
            CR = user_mention
            credit_display = f"{user_first_name} (no username)"
    else:
        CR = raw_text3
        credit_display = "Custom Name"
    
    # Show confirmation
    confirm_msg = await m.reply_text(f"✅ Credit set to: {CR}")
    await asyncio.sleep(1)
    await confirm_msg.delete()
    
    return CR
    
# Upload command handler
@bot.on_message(filters.command(["txt"]))
async def upload(bot: Client, m: Message):
    if not is_authorized(m.chat.id):
        await m.reply_text("**🚫You are not authorized to use this bot.**")
        return

    user_first_name = m.from_user.first_name
    user_last_name = m.from_user.last_name or ""
    user_full_name = f"{user_first_name} {user_last_name}".strip()
    user_username = m.from_user.username
    user_mention = f"<a href='tg://user?id={user_id}'>{user_full_name}</a>"
    
    editable = await m.reply_text(f"<pre><code> Send TXT File </code></pre>")
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
        await m.reply_text("<pre><code>Invalid file input.</code></pre>")
        os.remove(x)
        return

    
    await editable.edit(f"<pre><code>Total 🔗 links found are __{len(links)}\n\n🔹Img : {img_count}  🔹Pdf : {pdf_count}\n🔹Zip : {zip_count}  🔹Video : {video_count}__</code></pre>\n<pre><code>Send From where you want to download initial is `1`</code></pre>")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("<pre><code>**Enter Your Batch Name**</code></pre>\n<pre><code>Send `1` for use default.</code></pre>")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == '1':
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("<pre><code>╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ </code></pre>\n┣━━⪼ send `144`  for 144p\n┣━━⪼ send `240`  for 240p\n┣━━⪼ send `360`  for 360p\n┣━━⪼ send `480`  for 480p\n┣━━⪼ send `720`  for 720p\n┣━━⪼ send `1080` for 1080p\n<pre><code>╰━━⌈⚡[ 𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳 ]⚡⌋━━➣ </code></pre>")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    quality = input2.text
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

    # ========== CREDIT NAME SECTION (4 spaces indentation) ==========
    # Get credit name from user
    CR = await get_credit_name(
        bot, m, editable, user_id, 
        user_first_name, user_username, user_mention
    )
    # ========== END CREDIT NAME SECTION ==========

    cptoken = "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYzNjkyNjM0LCJvcmdJZCI6NjA5NzQyLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTk0MDQ0MDg3NDAiLCJuYW1lIjoiTXlyYSIsImVtYWlsIjoicml5YWhzaHJpdmFzdGF2NCs1MzMyQGdtYWlsLmNvbSIsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjoiRU4iLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpc0RpeSI6dHJ1ZSwibG9naW5WaWEiOiJPdHAiLCJmaW5nZXJwcmludElkIjoiODZmN2RhMjMyMzgxNDk2YTliMjY4YzhkMTAxOGNkMGEiLCJpYXQiOjE3NTkyMTA3ODksImV4cCI6MTc1OTgxNTU4OX0.O3DG_gMpOUet2HKSmH1jK9EEWmjREEMh4cX7DW4yqqkCTzcV5C6-lr6zaY1ihhR4"
    
    await editable.edit("<pre><code>**Enter CP or PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋**</code></pre>\n<pre><code>Send  `unknown`  for use default</code></pre>")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == '?':
        access_token = cptoken
    else:
        access_token = raw_text4
        
    await editable.edit("<pre><code>⚪Send ☞ jpg url for **Video Thumbnail** format</code></pre>\n<pre><code>🔘Send ☞ jpg url for **Document Thumbnail** format</code></pre>")
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

            
            elif 'contentId' in url or 'contentHashIdl=' in url:
                url = unquote(url)
                content = extract_id(url)
                
                encoded_content = urllib.parse.quote(content, safe="")
                
                headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': access_token,    
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
            

            
            

            if ".mp4?URLPrefix" in url or "/dash" in url:
                wake_player()
                url = pw_player(url)
                print("PW Player URL:", url)
                
            elif '/master.mpd' in url or "d1d34p8vz63oiq.cloudfront.net" in url or "parentId=" in url or "childId=" in url:
                video_url = await get_signed_videourl(url, access_token)
                print("PW Signed Url:", video_url)
                encoded_url = urllib.parse.quote(video_url, safe="")
                wake_player()
                url = f"https://learnwithpw-recorded.onrender.com/play?v={encoded_url}"
                
            elif 'content.allen.in' in url:
                url = convert_url(url, 'dash')
                fallback_url = convert_url(url, 'm3u8')
                print("First Change Url:", url)
                print("Fallback Change url:", fallback_url)



            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'

            
                
            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
                cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'
            else:
                
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'
            

            try:
                cc = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.mkv\n**├── Resolution :** [{res}]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                cc1 = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.pdf\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                html = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.pdf\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                
                cczip = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.zip\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                ccimg = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.jpg\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                ccyt = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n╭─────────────────.★..─╮\n   <a href="{url}">__**Click Here to Watch Stream**__</a>\n╰─..★.─────────────────╯\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.mkv\n**├── Resolution :** [{res}]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                ccukt = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n╭─────────────────.★..─╮\n   <a href="{url}">__**Click Here to Download**__</a>\n╰─..★.─────────────────╯\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakyaX.doc\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>'
                cpvod = f'**➭ Index » {str(count).zfill(3)}.\n\n\n➭ Title » {name1}.({res}).mkv\n\n\n🔗𝗩𝗶𝗱𝗲𝗼 𝗨𝗿𝗹 ➤ <a href="{url}">__Click Here to Watch Video__</a>\n\n➭ 𝐁𝐚𝐭𝐜𝐡 » {b_name}\n➭ Quality » {res}\n\n✨ 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘 {CR}**'
                
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

                # ==================== .ws FILE HANDLING ====================
                elif ".ws" in url.lower():
                    try:
                        cmd = f'{API_URL}/convert?url={url}'
                        os.system(cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.html', caption=html)
                        count += 1
                        os.remove(f'{name}.html')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue
                        
                        
                
                # ==================== PDF.pdf FILE HANDLING ====================
                elif "PDF.pdf" in url or "apps-s3-prod.utkarshapp.com/admin_v1/file_manager/pdf" in url:
                    try:
                        cmd = f'{API_URL}/pdf?url={url}'
                        os.system(cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue                
                        
                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue                
                        
                elif "*abcdefg" in url:
                    # ========================================================
                    # SECURE DECRYPTED PDF BYPASS ROUTER (Appx & Classx Decrypter)
                    # ========================================================
                    try:
                        
                        enc_key = "abcdefg"
                        downloaded_pdf = await encrypted_pdf(url, name, enc_key)

                        if downloaded_pdf and os.path.exists(downloaded_pdf):
                            copy = await bot.send_document(
                                chat_id=m.chat.id, 
                                document=downloaded_pdf, 
                                caption=cc1
                            )
                            count += 1
                            os.remove(downloaded_pdf)
                            print(f"[Success] Successfully decrypted and sent PDF: {downloaded_pdf}", flush=True)
                        else:
                            await m.reply_text(f"❌ **Failed to decrypt secure PDF:** Validation rejected or incorrect key.")
                            count += 1
                            failed_count += 1

                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(e.x)
                        continue
                    except Exception as e:
                        await m.reply_text(f"⚠️ PDF Decrypt Error: {str(e)}")
                        
                elif ".pdf?" in url:
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
                        
                elif "https://apps-s3-jw-prod.utkarshapp.com/admin_v1/file_library/videos" in url:
                    try:
                        api_endpoint = f"{API_URL}/video" 
                        file_name_with_ext = f"{name}.mp4"
                        
                        emoji_message = await show_random_emojis(m)
                        remaining_links = len(links) - count
                        Show = f"**🍁 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗𝗜𝗡𝗚 🍁**\n\n**📝ɴᴀᴍᴇ » ** `{name}\n\n🔗ᴛᴏᴛᴀʟ ᴜʀʟ » {len(links)}\n\n🗂️ɪɴᴅᴇ𝘅 » {str(count)}/{len(links)}\n\n🌐ʀᴇᴍᴀɪɴɪŋ ᴜʀʟ » {remaining_links}\n\n❄ǫᴜᴀʟɪᴛʏ » {res}`\n\n**🔗ᴜʀʟ » ** `{url}`\n\n**🎯 Bypass Mode Active (m3u8 check)**\n\n𝗕𝗢𝗧 𝗠𝗔𝗗Ｅ 𝗕𝗬 ➤ जाटⁱˢß𝐚𝐜𝐤ツ\n\n"
                        prog = await m.reply_text(Show)
                        
                        payload = {"url": url}
                        async with aiohttp.ClientSession() as session:
                            async with session.post(api_endpoint, json=payload, timeout=600) as response:
                                if response.status == 200:
                                    with open(file_name_with_ext, "wb") as f:
                                        async for chunk in response.content.iter_chunked(1024 * 1024):
                                            if chunk:
                                                f.write(chunk)
                                    
                                    res_file = file_name_with_ext
                                else:
                                    res_file = None

                        if res_file and os.path.exists(res_file):
                            filename = res_file
                            await prog.delete(True)
                            await emoji_message.delete()
                            await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                            count += 1
                            os.remove(file_name_with_ext)
                            time.sleep(1)
                        else:
                            await prog.delete(True)
                            await emoji_message.delete()
                            await m.reply_text(f"❌ **Downloading Failed!** Link validation blocked or expired.")
                            count += 1
                            failed_count += 1

                    except Exception as e:
                        if 'prog' in locals():
                            await prog.delete(True)
                        if 'emoji_message' in locals():
                            await emoji_message.delete()
                            
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


bot.run()
