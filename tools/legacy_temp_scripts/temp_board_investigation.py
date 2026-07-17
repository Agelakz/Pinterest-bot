import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinpapantest.har', 'r') as f:
    har = json.load(f)

print("=== ALL BOARD RELATED REQUESTS ===")
for idx, entry in enumerate(har['log']['entries']):
    req = entry['request']
    url = req['url']
    method = req['method']
    
    # Kumpulkan endpoint yang punya resource 'Board', 'search', 'boards' dll.
    if 'ApiResource' in url or 'Board' in unquote(req.get('postData', {}).get('text', '')):
        post_data = req.get('postData', {}).get('text', '')
        decoded = unquote(post_data)
        
        # Filter spesifik Board operations (picker, search, create)
        if 'board' in decoded.lower():
            print(f"[{idx}] {method} {url}")
            print(f"PAYLOAD: {decoded}")
            print(f"RESPONSE (Truncated): {entry['response']['content'].get('text', '')[:500]}...")
            print("-" * 50)
