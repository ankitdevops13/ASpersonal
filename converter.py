import os
import gzip
import urllib.request
import urllib.error

def download_html(url, name):
    """
    Urllib client ka use karke strict Cloudflare/S3 bypass 
    aur print-ready A4 HTML generation.
    """
    html_filename = f"{name}.html"
    
    # Raw headers setup jo strictly regular browser traffic mirror karega
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
        "Sec-Fetch-Site": "cross-site",
        "Connection": "keep-alive"
    }
    
    try:
        # Request module ka use bina kisi Python automation metadata ke
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read()
            
            # Check for GZIP encoding automatically via header content or byte format
            content_encoding = response.info().get('Content-Encoding')
            if content_encoding == 'gzip' or raw_data.startswith(b'\x1f\x8b'):
                decompressed_data = gzip.decompress(raw_data).decode('utf-8', errors='ignore')
            else:
                decompressed_data = raw_data.decode('utf-8', errors='ignore')

    except urllib.error.HTTPError as e:
        # Fallback agar unka secure edge standard fetch blocks check kare
        raise Exception(f"S3 Security Blocked (HTTP {e.code}): Headers/Token change required.")
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

    # HTML file local storage me save karna
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return html_filename
    
