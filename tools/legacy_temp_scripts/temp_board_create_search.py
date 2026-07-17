import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinpapantest.har', 'r') as f:
    har = json.load(f)

for idx, entry in enumerate(har['log']['entries']):
    req = entry['request']
    url = req['url']
    
    # Check for BoardResource create action
    if 'BoardResource/create' in url or 'BoardResource' in unquote(req.get('postData', {}).get('text', '')):
        print(f"\n=== POTENTIAL BOARD CREATE ===")
        print(f"URL: {unquote(url)}")
        print(f"PAYLOAD: {unquote(req.get('postData', {}).get('text', ''))}")
        
    # Look for the exact new board ID '972285075743712936' which was published to
    if '972285075743712936' in unquote(req.get('postData', {}).get('text', '')):
        print(f"\n=== REQUEST CONTAINING NEW BOARD ID ===")
        print(f"URL: {unquote(url)}")
        print(f"PAYLOAD (truncated): {unquote(req.get('postData', {}).get('text', ''))[:300]}")
