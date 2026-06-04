# Don't Remove Credit Tg - @Tushar0125

import os
import time
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures

from utils import progress_bar

from pyrogram import Client, filters
from pyrogram.types import Message

from pytube import Playlist  # Youtube Playlist Extractor
from yt_dlp import YoutubeDL
import yt_dlp as youtube_dl


def duration(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)


def exec(cmd):
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.stdout.decode()
    print(output)
    return output


def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec, cmds)


async def aio(url, name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k


async def download(url, name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka


def parse_vid_info(info):
    info = info.strip().split("\n")
    new_info = []
    temp = []
    for i in info:
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i = i.strip().split("|")[0].split(" ", 2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info


def vid_info(info):
    info = info.strip().split("\n")
    new_info = dict()
    temp = []
    for i in info:
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i = i.strip().split("|")[0].split(" ", 3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info[f'{i[2]}'] = f'{i[0]}'
            except:
                pass
    return new_info


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'


def old_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


def get_playlist_videos(playlist_url):
    try:
        playlist = Playlist(playlist_url)
        playlist_title = playlist.title
        videos = {}
        for video in playlist.videos:
            try:
                video_title = video.title
                video_url = video.watch_url
                videos[video_title] = video_url
            except Exception as e:
                logging.error(f"Could not retrieve video details: {e}")
        return playlist_title, videos
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None, None


def get_all_videos(channel_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }

    all_videos = []
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)

        if 'entries' in result:
            channel_name = result['title']
            all_videos.extend(result['entries'])

            video_links = {index + 1: (video['title'], video['url']) for index, video in enumerate(all_videos)}
            return video_links, channel_name
        else:
            return None, None


def save_to_file(video_links, channel_name):
    import re
    sanitized_channel_name = re.sub(r'[^\w\s-]', '', channel_name).strip().replace(' ', '_')
    filename = f"{sanitized_channel_name}.txt"
    with open(filename, 'w', encoding='utf-8') as file:
        for number, (title, url) in video_links.items():
            if url.startswith("https://"):
                formatted_url = url
            elif "shorts" in url:
                formatted_url = f"https://www.youtube.com{url}"
            else:
                formatted_url = f"https://www.youtube.com/watch?v={url}"
            file.write(f"{number}. {title}: {formatted_url}\n")
    return filename

async def download_secure_pdf(url, name):
    clean_name = f"{name}.pdf" if not name.endswith(".pdf") else name
    print(f"[Secure PDF] Download suru ho raha hai: {clean_name}", flush=True)
    
    # Termux bypass headers ke sath curl command
    cmd = [
        "curl", "-L",
        "-H", "User-Agent: Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "-H", "Referer: https://appx-play.akamai.net.in/",
        "-o", clean_name,
        url
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode == 0 and os.path.exists(clean_name):
            print(f"[Secure PDF] Download safal raha: {clean_name}", flush=True)
            return clean_name
        else:
            print("[Secure PDF] Error: Curl download process fail ho gaya.", flush=True)
            return None
    except Exception as e:
        print(f"[Secure PDF] Exception error: {str(e)}", flush=True)
        return None
        
async def download_secure_video(url, name):
    """
    Yeh function normal HLS (.m3u8) video streams ko bypass headers ke sath download aur copy karta hai.
    """
    clean_name = f"{name}.mp4" if not name.endswith(".mp4") else name
    print(f"[Secure Video] Stream compile hona suru ho gaya hai: {clean_name}", flush=True)
    
    # Normal stream fetch karne ke liye bypass ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-user_agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "-headers", "Referer: https://appx-play.akamai.net.in/",
        "-i", url,
        "-c", "copy",
        clean_name
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        
        # Live conversion logs console par show karne ke liye loop
        while True:
            line_bytes = await process.stderr.readline()
            if not line_bytes:
                break
            line = line_bytes.decode(errors='ignore').strip()
            print(f"[Secure Video Process] {line}", flush=True)
            
        await process.wait()
        
        if process.returncode == 0 and os.path.exists(clean_name):
            print(f"[Secure Video] Conversion complete ho gaya: {clean_name}", flush=True)
            return clean_name
        else:
            print("[Secure Video] Error: FFmpeg run completed with failure.", flush=True)
            return None
    except Exception as e:
        print(f"[Secure Video] Exception error: {str(e)}", flush=True)
        return None
        
# ✅ Updated download_video with fallback if aria2c fails
async def download_video(url, cmd, name):
    global failed_counter

    aria2c_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    fallback_cmd = f'{cmd} -R 10 --fragment-retries 10'

    for attempt in range(2):  # Try twice: first with aria2c, then without
        logging.info(f"[Download Attempt {attempt + 1}] Running command: {aria2c_cmd if attempt == 0 else fallback_cmd}")
        selected_cmd = aria2c_cmd if attempt == 0 else fallback_cmd
        result = subprocess.run(selected_cmd, shell=True)
        if result.returncode == 0:
            break
        await asyncio.sleep(2)

    # Check for common file outputs
    for ext in ["", ".webm", ".mp4", ".mkv", ".mp4.webm"]:
        target_file = name + ext
        if os.path.isfile(target_file):
            return target_file

    return name


async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name):
    reply = await m.reply_text(f"🚀🚀🚀𝗨𝗣𝗟𝗢𝗔𝗗𝗜𝗡𝗚🚀🚀🚀 » `{name}`\n\n🤖𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 ➤ जाटⁱˢß𝐚𝐜𝐤ツ ")
    time.sleep(1)
    start_time = time.time()
    await m.reply_document(ka, caption=cc1)
    count += 1
    await reply.delete(True)
    time.sleep(1)
    os.remove(ka)
    time.sleep(3)


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:12 -vframes 1 "{filename}.jpg"', shell=True)
    await prog.delete(True)
    reply = await m.reply_text(f"**🚀🚀🚀𝗨𝗣𝗟𝗢𝗔𝗗𝗜𝗡𝗚🚀🚀🚀** » `{name}`\n\n🤖𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 ➤ जाटⁱˢß𝐚𝐜𝐤ツ ")
    try:
        thumbnail = f"{filename}.jpg" if thumb == "no" else thumb
    except Exception as e:
        await m.reply_text(str(e))
        return

    dur = int(duration(filename))
    start_time = time.time()

    try:
        await m.reply_video(filename, caption=cc, supports_streaming=True, height=720, width=1280,
                            thumb=thumbnail, duration=dur,
                            progress=progress_bar, progress_args=(reply, start_time))
    except Exception:
        await m.reply_document(filename, caption=cc, progress=progress_bar, progress_args=(reply, start_time))

    os.remove(filename)
    os.remove(f"{filename}.jpg")
    await reply.delete(True)
