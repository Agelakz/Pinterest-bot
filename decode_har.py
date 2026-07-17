import json
import urllib.parse
with open('api_creates.json') as f:
    data = json.load(f)
    for i, req in enumerate(data):
        if 'postData' in req and req['postData']:
            parsed = urllib.parse.parse_qs(req['postData'])
            if 'data' in parsed:
                try:
                    js = json.loads(parsed['data'][0])
                    url = js.get('options', {}).get('url', 'UNKNOWN')
                    print(f"Request {i}: {url}")
                except Exception as e:
                    print(f"Request {i}: ERROR {e}")
