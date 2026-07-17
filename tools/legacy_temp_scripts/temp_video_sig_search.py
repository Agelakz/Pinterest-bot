import json

with open('/home/ubuntu/pinterest-bot/pinvideotest.har', 'r') as f:
    har = json.load(f)

search_value = "b7fe9e3a2bbaea4758f419529f145d55"
found = False

print(f"Searching for '{search_value}' in all HAR entries...")

for idx, entry in enumerate(har['log']['entries']):
    # Search in request URL
    url = entry['request']['url']
    if search_value in url:
        print(f"Found in Request URL (Entry {idx}): {url}")
        found = True

    # Search in request headers
    for header in entry['request']['headers']:
        if search_value in header['value']:
            print(f"Found in Request Header {header['name']} (Entry {idx})")
            found = True

    # Search in request postData
    post_data = entry['request'].get('postData', {}).get('text', '')
    if post_data and search_value in post_data:
        print(f"Found in Request POST Data (Entry {idx}): {url}")
        found = True

    # Search in response headers
    for header in entry['response']['headers']:
        if search_value in header['value']:
            print(f"Found in Response Header {header['name']} (Entry {idx}): {url}")
            found = True

    # Search in response content
    resp_content = entry['response']['content'].get('text', '')
    if resp_content and search_value in resp_content:
        print(f"Found in Response Content (Entry {idx}): {url}")
        found = True

if not found:
    print("NOT FOUND anywhere else in the HAR file.")
