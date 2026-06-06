import os
import gzip
import urllib.request
import urllib.error

# ⚠️ APNI LATEST COOKIE YAHA PASTE KAREIN (Screenshot 2 me jo badi si string hai)
# Agar 403 error aaye, to browser ke Network tab se nayi cookie copy karke yaha dalein.
UTKARSH_COOKIE = "_gcl_au=1.1.2026467561.1780740007; _gid=GA1.2.309059237.1780740008; _ga=GA1.1.2127262317.1780740008; csrf_name=12c2541d50bece75b3b905b484dc446d; ci_session=ub88g7bmr9knopo0o9eeepj0mdrmr6bk; rzp_unified_session_id=SyKWYYGsBUTCpI"

def download_html(url, name):
    """
    Cookie aur Strict Headers ka use karke S3 Security bypass 
    aur print-ready A4 HTML generation.
    """
    html_filename = f"{name}.html"
    
    # Strict Session Headers aur Cookie integration
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Cookie": UTKARSH_COOKIE,  # <--- Yeh sabse zaroori hai bypass ke liye
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
    
    try:
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read()
            
            # GZIP handling
            content_encoding = response.info().get('Content-Encoding')
            if content_encoding == 'gzip' or raw_data.startswith(b'\x1f\x8b'):
                decompressed_data = gzip.decompress(raw_data).decode('utf-8', errors='ignore')
            else:
                decompressed_data = raw_data.decode('utf-8', errors='ignore')

    except urllib.error.HTTPError as e:
        raise Exception(f"S3 Security Blocked (HTTP {e.code}): Cookie expire ho gayi hai, nayi daalna padega.")
    except Exception as e:
        raise Exception(f"Download Error: {str(e)}")

    # Print-Ready A4 HTML Layout template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        body {{
            background-color: #525659;
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .a4-page {{
            background: #ffffff;
            width: 210mm;
            min-height: 297mm;
            padding: 20mm;
            margin: 10px auto;
            box-sizing: border-box;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        h2 {{
            color: #007bff;
            font-size: 22px;
            margin-top: 0;
            border-bottom: 2px solid #007bff;
            padding-bottom: 8px;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.6;
            color: #222;
            margin: 0;
        }}
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
    
