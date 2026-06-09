import os
import gzip
import tempfile
import urllib.request
import urllib.error
from urllib.parse import urlparse
import requests
import traceback
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

UTKARSH_COOKIE = "YOUR_COOKIE_HERE"


def register_cleanup(response, file_path):

    @response.call_on_close
    def cleanup():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Cleanup Error: {e}")

    return response



def download_file(url, filename=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Origin": "https://online.utkarsh.com",
        "Referer": "https://online.utkarsh.com/"
    }

    try:
        # Use stream=True for large files (videos)
        response = requests.get(url, headers=headers, stream=True, timeout=120)
        response.raise_for_status()
        
        # Get the raw content
        raw_data = response.content
        
        print(f"Downloaded {len(raw_data)} bytes")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")
        print(f"Status Code: {response.status_code}")
        
        # Check if the data is gzip compressed
        if raw_data.startswith(b'\x1f\x8b'):
            print("✅ Detected gzip compressed data - decompressing...")
            try:
                raw_data = gzip.decompress(raw_data)
                print(f"Decompressed to {len(raw_data)} bytes")
            except Exception as e:
                print(f"⚠️ Gzip decompression failed: {e}")
                # If decompression fails, keep original data
                pass
        
        if not filename:
            filename = (
                os.path.basename(urlparse(url).path)
                or "downloaded_file"
            )

        # Ensure proper extension
        if not filename.endswith('.mp4'):
            filename += '.mp4'

        file_path = os.path.join(
            tempfile.gettempdir(),
            filename
        )

        with open(file_path, "wb") as f:
            f.write(raw_data)
        
        print(f"✅ Saved file to: {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text[:500]}")
        raise Exception(f"Download failed: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {traceback.format_exc()}")
        raise


def download_file2(url, filename=None):

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Origin": "https://online.utkarsh.com",
        "Referer": "https://online.utkarsh.com/",
        "Sec-Ch-Ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": '"Android"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive"
    }

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=60) as response:

        if not filename:
            filename = (
                os.path.basename(urlparse(url).path)
                or "downloaded_file"
            )

        file_path = os.path.join(
            tempfile.gettempdir(),
            filename
        )

        with open(file_path, "wb") as f:
            f.write(response.read())

    return file_path


def process_ws_file(url, name):

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Origin": "https://online.utkarsh.com",
        "Referer": "https://online.utkarsh.com/",
        "Sec-Ch-Ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": '"Android"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive"
    }

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=30) as response:

        raw_data = response.read()

        if (
            response.info().get("Content-Encoding") == "gzip"
            or raw_data.startswith(b"\x1f\x8b")
        ):
            content = gzip.decompress(raw_data).decode(
                "utf-8",
                errors="ignore"
            )
        else:
            content = raw_data.decode(
                "utf-8",
                errors="ignore"
            )

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{name}</title>
<style>
body {{
    font-family: Arial;
    margin: 30px;
}}
pre {{
    white-space: pre-wrap;
    word-wrap: break-word;
}}
</style>
</head>
<body>
<h2>{name}</h2>
<pre>{content}</pre>
</body>
</html>
"""

    html_file = os.path.join(
        tempfile.gettempdir(),
        f"{name}.html"
    )

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_file


@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "routes": [
            "/convert",
            "/pdf",
            "/video"
        ]
    })


@app.route("/convert", methods=["GET", "POST"])
def convert():

    data = (
        request.get_json(silent=True)
        or request.form
    )

    url = (
        data.get("url")
        if request.method == "POST"
        else request.args.get("url")
    )

    name = (
        data.get("name", "notes")
        if request.method == "POST"
        else request.args.get("name", "notes")
    )

    if not url:
        return jsonify({
            "error": "url missing"
        }), 400

    try:

        html_file = process_ws_file(url, name)

        response = send_file(
            html_file,
            as_attachment=True,
            download_name=f"{name}.html"
        )

        return register_cleanup(
            response,
            html_file
        )

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500



@app.route("/pdf", methods=["GET", "POST"])
def pdf():
    data = (
        request.get_json(silent=True)
        or request.form
    )

    url = (
        data.get("url")
        if request.method == "POST"
        else request.args.get("url")
    )

    if not url:
        return jsonify({
            "error": "url missing"
        }), 400

    try:
        print(f"\n📥 Downloading PDF from: {url}")
        
        pdf_file = download_file(url, "document.pdf")

        response = send_file(
            pdf_file,
            as_attachment=True,
            download_name="document.pdf",
            mimetype="application/pdf"
        )

        return register_cleanup(response, pdf_file)

    except Exception as e:
        print(f"❌ PDF error: {traceback.format_exc()}")
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/video", methods=["GET", "POST"])
def video():
    data = (
        request.get_json(silent=True)
        or request.form
    )

    url = (
        data.get("url")
        if request.method == "POST"
        else request.args.get("url")
    )

    name = (
        data.get("name", "video.mp4")
        if request.method == "POST"
        else request.args.get("name", "video.mp4")
    )

    if not url:
        return jsonify({
            "error": "url missing"
        }), 400

    try:
        print(f"\n📥 Downloading Video from: {url}")
        
        # Ensure proper extension
        if not name.endswith('.mp4'):
            name += '.mp4'
            
        video_file = download_file(url, name)

        response = send_file(
            video_file,
            as_attachment=True,
            download_name=name,
            mimetype="video/mp4"
        )

        return register_cleanup(response, video_file)

    except Exception as e:
        print(f"❌ Video error: {traceback.format_exc()}")
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    # Install requests: pip install requests
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
