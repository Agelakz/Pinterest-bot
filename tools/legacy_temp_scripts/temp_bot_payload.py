import ast
import json

with open('/home/ubuntu/pinterest-bot/services/pinterest_api.py', 'r') as f:
    source = f.read()

# very basic extraction by finding 'story_pin_meta ='
start = source.find('story_pin_meta = {')
if start != -1:
    end = source.find('            }', start) + 13
    dict_str = source[start:end].replace('story_pin_meta = ', '').strip()
    print("BOT DICT LITERAL:")
    print(dict_str)
