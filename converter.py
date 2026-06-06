import os
import gzip
import requests

def download_html(url, name):
    """
    Utkarsh .ws file ko Android Headers ke sath download karke 
    print-ready A4 HTML file me convert karti hai.
    """
    html_filename = f"{name}.html"
    
    # Android Device ke fake headers taaki 403 Forbidden Error na aaye
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    # 1. File download karna (with headers)
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status() # Agar ab bhi koi error aayi to ye catch ho jayegi
    raw_data = response.content

    # 2. Gzip Decompression logic
    try:
        if raw_data.startswith(b'\x1f\x8b'):
            decompressed_data = gzip.decompress(raw_data).decode('utf-8', errors='ignore')
        else:
            decompressed_data = raw_data.decode('utf-8', errors='ignore')
    except Exception:
        decompressed_data = raw_data.decode('utf-8', errors='ignore')

    # 3. Print-Ready A4 HTML Layout template
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

    # 4. HTML file local storage me save karna
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return html_filename
    
