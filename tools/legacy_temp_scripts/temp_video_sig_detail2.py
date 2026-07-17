import json

with open('/home/ubuntu/pinterest-bot/pinvideotest.har', 'r') as f:
    har = json.load(f)

entry_19 = har['log']['entries'][19]
resp_19 = json.loads(entry_19['response']['content']['text'])

print("Where is the signature in Entry 19?")
data = resp_19.get('resource_response', {}).get('data', {})
for k, v in data.items():
    if k == "3682736856317653568":
        print(f"upload_id: {v.get('upload_id')}")
        print(f"status: {v.get('status')}")
        print(f"signature: {v.get('signature')}")
        print(f"type: {v.get('type')}")
