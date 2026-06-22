import asyncio
import aiohttp
import re

async def get_signed_video_url(access_token, parent_id, child_id):
    if not access_token.startswith("Bearer "):
        access_token = f"Bearer {access_token}"

    headers = {
        'Host': 'api.penpencil.co',
        'Authorization': access_token,
        'Client-Id': '5eb393ee95fab7468a79d189',
        'Client-Type': 'WEB',
        'Client-Version': '1.0.0',
        'Content-Type': 'application/json',
        'Randomid': 'becda3bb-3759-4a7a-a75a-129010ce2067',
        'Origin': 'https://www.pw.live',
        'Referer': 'https://www.pw.live/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        'X-Sdk-Version': '0.0.20'
    }

    api_url = (
        "https://api.penpencil.co/v1/videos/video-url-details"
        f"?type=BATCHES"
        f"&videoContainerType=DASH"
        f"&reqType=query"
        f"&childId={child_id}"
        f"&parentId={parent_id}"
        f"&clientVersion=201"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as resp:

            print(f"\n[+] Status Code: {resp.status}")

            if resp.status != 200:
                print(await resp.text())
                return None

            data = await resp.json()

            if not data.get("success"):
                print(data)
                return None

            video_data = data.get("data", {})

            base_url = video_data.get("url")
            signed_part = video_data.get("signedUrl")

            if not base_url:
                print("[-] Base URL not found")
                return None

            if signed_part:
                return base_url + signed_part

            return base_url


def extract_ids(url):
    parent_match = re.search(r'parentId=([a-zA-Z0-9]+)', url)
    child_match = re.search(r'childId=([a-zA-Z0-9]+)', url)

    parent_id = parent_match.group(1) if parent_match else None
    child_id = child_match.group(1) if child_match else None

    return parent_id, child_id


async def main():

    video_url = input("Enter Full URL: ").strip()
    token = input("Enter Access Token: ").strip()

    parent_id, child_id = extract_ids(video_url)

    if not parent_id:
        print("[-] parentId not found")
        return

    if not child_id:
        print("[-] childId not found")
        return

    print(f"\n[+] Parent ID: {parent_id}")
    print(f"[+] Child ID : {child_id}")

    print("\n[+] Fetching signed URL...")

    final_url = await get_signed_video_url(
        token,
        parent_id,
        child_id
    )

    if final_url:
        print("\n" + "=" * 80)
        print("FINAL SIGNED URL")
        print("=" * 80)
        print(final_url)
        print("=" * 80)
    else:
        print("\n[-] Failed")


if __name__ == "__main__":
    asyncio.run(main())
