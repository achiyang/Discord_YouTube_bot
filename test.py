import json

with open("data/youtube_channels.json", "r")as f:
    youtube_chhannels = json.load(f)

for channel_id in youtube_chhannels:
    youtube_chhannels[channel_id] = {
        "channel_name": youtube_chhannels[channel_id]["channel_name"],
        "channel_image_url": youtube_chhannels[channel_id]["channel_image_url"],
        "channel_description": youtube_chhannels[channel_id]["channel_description"],
        "video_id": youtube_chhannels[channel_id]["video_id"]
    }

with open("data/youtube_channels.json", "w")as f:
    json.dump(youtube_chhannels, f, indent=4)