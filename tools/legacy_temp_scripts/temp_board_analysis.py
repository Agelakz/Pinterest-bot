import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinpapantest.har', 'r') as f:
    har = json.load(f)

for idx, entry in enumerate(har['log']['entries']):
    req = entry['request']
    url = req['url']
    
    if 'BoardPickerBoardsResource' in url:
        print(f"=== BOARD PICKER REQUEST ===")
        print(f"URL: {unquote(url)}")
        resp = json.loads(entry['response']['content']['text'])
        data = resp.get('resource_response', {}).get('data', {})
        boards = data.get('all_boards', [])
        shortlist = data.get('boards_shortlist', [])
        print(f"Found {len(boards)} boards in all_boards.")
        for b in boards:
            print(f" - {b.get('id')} | {b.get('name')} | {b.get('type')}")
            
    if 'BoardCreateClass' in unquote(req.get('postData', {}).get('text', '')):
        print(f"\n=== BOARD CREATE EVENT ===")
        print(f"URL: {unquote(url)}")
        print(f"PAYLOAD: {unquote(req['postData']['text'])}")
        
