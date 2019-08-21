import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

restaurant_mappings = {}
for filename in os.listdir("./reviews/"):
    restaurant = filename.split(".")[0]
    print(restaurant)
    try: 
        source = requests.get("https://www.yelp.com/biz/"+restaurant)
        soup = BeautifulSoup(source.content, features = "html.parser")
        title_raw = str(soup.find("meta",  property="og:title"))
        title_extracted = re.findall("<.+>\n", title_raw)[0]
        new_soup = BeautifulSoup(title_extracted)
        restaurant_info = new_soup.findAll("meta")[0].get("content")
        restaurant_name = re.findall("(.+?) - .+", restaurant_info)[0]
        print(restaurant_name)
        restaurant_mappings[restaurant_name] = restaurant
    except:
        print("Failed to find name")

with open("mappings.json", "w+") as f:
    json.dump(restaurant_mappings, f)