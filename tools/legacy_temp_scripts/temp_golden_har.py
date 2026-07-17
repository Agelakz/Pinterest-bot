import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinvideotest.har', 'r') as f:
    har = json.load(f)

print("=== 1. MEDIA UPLOADS REGISTER ===")
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'ApiResource' in url:
        post_data = entry['request'].get('postData', {}).get('text', '')
        if 'register%2Fbatch' in post_data or 'register/batch' in unquote(post_data):
            try:
                decoded = unquote(post_data)
                print("REQUEST:", decoded)
                resp = entry['response']['content']['text']
                print("RESPONSE:", resp)
                print("-" * 40)
            except Exception as e:
                pass

print("\n=== 2. FINAL PUBLISH (v3/storypins/) ===")
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'ApiResource' in url:
        post_data = entry['request'].get('postData', {}).get('text', '')
        if 'v3%2Fstorypins%2F' in post_data and 'drafts' not in post_data:
            try:
                decoded = unquote(post_data)
                print("REQUEST:", decoded)
                resp = entry['response']['content']['text']
                print("RESPONSE:", resp)
                print("-" * 40)
            except Exception as e:
                pass
