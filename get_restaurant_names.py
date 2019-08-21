import re
import os
import json

restaurants = {}
for rest in os.listdir('./menu_items/'):
    if rest[0] == ".":
        continue
    alias = rest[:-4]
    name = re.findall("(.+)-san-francisco", alias)[0].replace('-', ' ')
    restaurants[alias] = name

with open('restaurant_mappings.json', 'w+') as f:
    json.dump(restaurants, f)