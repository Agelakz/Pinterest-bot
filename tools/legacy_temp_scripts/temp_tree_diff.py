import json

browser_str = '{"metadata":{"pin_title":"test","pin_image_signature":"5a14f93aab3366250e1c961f6f213d25","canvas_aspect_ratio":0.651685393258427},"pages":[{"blocks":[{"block_style":{"height":100,"width":100,"x_coord":0,"y_coord":0},"tracking_id":"3682736856317653568","video_signature":"b7fe9e3a2bbaea4758f419529f145d55","type":3}],"clips":[{"clip_type":1,"end_time_ms":-1,"is_converted_from_image":false,"source_media_height":1780,"source_media_width":1160,"start_time_ms":-1}],"layout":0,"style":{"background_color":"#FFFFFF"}}]}'
bot_str = '{"metadata":{"pin_title":"Title Dinamis","pin_image_signature":"5a14f93aab3366250e1c961f6f213d25","canvas_aspect_ratio":0.5625},"pages":[{"blocks":[{"block_style":{"height":100,"width":100,"x_coord":0,"y_coord":0},"tracking_id":"3682773165602612032","video_signature":"d06bad51ff775728c1f3680f479c335f","type":3}],"clips":[{"clip_type":1,"end_time_ms":-1,"is_converted_from_image":false,"source_media_height":1920,"source_media_width":1080,"start_time_ms":-1}],"layout":0,"style":{"background_color":"#FFFFFF"}}]}'

browser_json = json.loads(browser_str)
bot_json = json.loads(bot_str)

print("BROWSER JSON TREE:")
print(json.dumps(browser_json, indent=2))
print("\nBOT JSON TREE:")
print(json.dumps(bot_json, indent=2))
