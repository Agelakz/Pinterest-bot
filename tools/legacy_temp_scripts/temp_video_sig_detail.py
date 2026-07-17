import json
from urllib.parse import unquote

with open('/home/ubuntu/pinterest-bot/pinvideotest.har', 'r') as f:
    har = json.load(f)

search_value = "b7fe9e3a2bbaea4758f419529f145d55"

print(f"=== ETag from Entry 7 (S3 Upload Response) ===")
s3_entry = har['log']['entries'][7]
for header in s3_entry['response']['headers']:
    if header['name'].lower() == 'etag':
        print(f"ETag: {header['value']}")
        
print(f"\n=== Content from Entry 19 (ApiResource/get) ===")
entry_19 = har['log']['entries'][19]
print("URL:", unquote(entry_19['request']['url']))
print("RESPONSE (truncated):")
resp_19 = json.loads(entry_19['response']['content']['text'])
print(json.dumps(resp_19, indent=2)[:500] + "\n...")

print("\nWhere is the signature in Entry 19?")
data = resp_19.get('resource_response', {}).get('data', [])
for d in data:
    if d.get('upload_id') == "3682736856317653568":
        print(f"upload_id: {d.get('upload_id')}")
        print(f"status: {d.get('status')}")
        print(f"media_id: {d.get('media_id')}")
        print(f"media_signature: {d.get('media_signature')}")
        print(f"type: {d.get('type')}")
