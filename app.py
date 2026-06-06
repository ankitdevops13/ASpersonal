import os
import gzip
import urllib.request
import urllib.error
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# JAB BHI 403 ERROR AAYE, APNE BROWSER SE NEW COOKIE NIKAL KAR YAHA PASTE KAREIN
UTKARSH_COOKIE = "_gcl_au=1.1.2026467561.1780740007; _gid=GA1.2.309059237.1780740008; _ga=GA1.1.2127262317.1780740008; csrf_name=12c2541d50bece75b3b905b484dc446d; ci_session=ub88g7bmr9knopo0o9eeepj0mdrmr6bk; rzp_unified_session_id=SyKWYYGsBUTCpI"

def process_ws_file(url, name):
    html_filename = f"{name}.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Cookie": UTKARSH_COOKIE,
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
        content_encoding = response.info().get('Content-Encoding')
        
        if content_encoding == 'gzip' or raw_data.startswith(b'\x1f\x8b'):
            decompressed_data = gzip.decompress(raw_data).decode('utf-8', errors='ignore')
        else:
            decompressed_data = raw_data.decode('utf-8', errors='ignore')

    # A4 Layout HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        body {{ background-color: #525659; margin: 0; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; display: flex; flex-direction: column; align-items: center; }}
        .a4-page {{ background: #ffffff; width: 210mm; min-height: 297mm; padding: 20mm; margin: 10px auto; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
        h2 {{ color: #007bff; font-size: 22px; margin-top: 0; border-bottom: 2px solid #007bff; padding-bottom: 8px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 14px; line-height: 1.6; color: #222; margin: 0; }}
        @media print {{
            body {{ background: none; padding: 0; }}
            .a4-page {{ width: 100%; height: auto; margin: 0; padding: 0; box-shadow: none; }}
            @page {{ size: A4; margin: 15mm; }}
        }}
    </style>
</head>
<body>
    <div class="a4-page">
        <h2>{name}</h2>
        <pre>{decompressed_data}</pre>
    </div>
</body>
</html>"""

    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return html_filename


@app.route('/')
def home():
    # Yeh check karne ke liye ki API up hai ya nahi
    return jsonify({"status": "running", "message": "API ekdum mast chal rahi hai!"})


@app.route('/convert', methods=['GET', 'POST'])
def convert_api():
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or request.form
            url = data.get('url')
            name = data.get('name', 'utkarsh_notes')
        else:
            url = request.args.get('url')
            name = request.args.get('name', 'utkarsh_notes')

        if not url:
            return jsonify({"status": "error", "message": "URL parameter missing hai bhai!"}), 400

        generated_file = process_ws_file(url, name)
        
        # File response bhejna
        return send_file(generated_file, as_attachment=True, download_name=generated_file)

    except urllib.error.HTTPError as e:
        return jsonify({
            "status": "error", 
            "error_code": e.code,
            "message": "Utkarsh S3 ne block kiya (403 Forbidden). UTKARSH_COOKIE badalna padega."
        }), 403
    except Exception as e:
        # Yeh line kisi bhi internal error ko json me dikha degi (Page crash nahi hoga)
        return jsonify({"status": "error", "message": f"Internal Error: {str(e)}"}), 500


if __name__ == '__main__':
    # Yeh local testing ke liye hai, Render ise use nahi karega agar gunicorn on hai
    port = int(os.environ.get("PORT", 1000))
    app.run(host='0.0.0.0', port=port)
    
