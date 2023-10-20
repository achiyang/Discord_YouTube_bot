import json
import os

def sort_videos():
    os.chdir(os.path.realpath(os.path.dirname(os.path.dirname(__file__))))

    with open("data/youtube_channels.json", "r") as f:
        youtube_channels = json.load(f)

    for channel_id in youtube_channels:
        sorted_dict = dict(sorted(youtube_channels[channel_id]["video_id"].items(), key=lambda item: item[1]["published"], reverse=True))
        youtube_channels[channel_id]["video_id"] = sorted_dict

    with open("data/youtube_channels.json", "w") as f:
        json.dump(youtube_channels, f, indent=4)

if __name__ == "__main__":
    sort_videos()