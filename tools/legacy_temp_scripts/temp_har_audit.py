import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinpapantest.har', 'r') as f:
    har = json.load(f)

for idx, entry in enumerate(har['log']['entries']):
    req = entry['request']
    if 'BoardPickerBoardsResource/get' in req['url']:
        print("=== BROWSER REQUEST ===")
        print("URL:", req['url'])
        print("HEADERS:")
        for h in req['headers']:
            if h['name'].lower() not in ['cookie']:
                print(f"  {h['name']}: {h['value']}")
        break
