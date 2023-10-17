import json

with open("data/youtube_channels.json", "r")as f:
    y = json.load(f)

for channel in y:
    for video in y[channel]["video_id"]:
        if "title" in y[channel]["video_id"][video]:
            del y[channel]["video_id"][video]["title"]

with open("data/youtube_channels.json", "w")as f:
    json.dump(y, f, indent=4)