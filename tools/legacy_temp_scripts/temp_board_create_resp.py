import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinpapantest.har', 'r') as f:
    har = json.load(f)

for idx, entry in enumerate(har['log']['entries']):
    req = entry['request']
    url = req['url']
    
    if 'BoardResource/create' in url:
        print(f"=== BOARD CREATE RESPONSE ===")
        print(json.dumps(json.loads(entry['response']['content']['text']), indent=2)[:800])
