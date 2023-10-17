import json
import requests
import feedparser

response = requests.request("GET", "https://www.youtube.com/feeds/videos.xml?channel_id=UC1iA6_NT4mtAcIII6ygrvCw", allow_redirects=True)
parse = feedparser.parse(response.text)

with open("test.json", "w")as f:
    json.dump(parse, f, indent=4)