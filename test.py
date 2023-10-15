import aiohttp
import asyncio
import feedparser
import json
import os

async def fetch_youtube_video(channel_id, count: int = 0) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}', allow_redirects=True) as response:
            if response.status == 200:
                video_ids = {}
                data = await response.text()
                feed = await asyncio.to_thread(feedparser.parse, data)
                for i in range(len(feed["entries"])):
                    video_id = feed["entries"][i]["yt_videoid"]
                    if feed["entries"][i]["updated_parsed"]:
                        updated = feed["entries"][i]["updated_parsed"]
                        video_ids[video_id] = updated
                    else:
                        published = feed["entries"][i]["published_parsed"]
                        video_ids[video_id] = published
                    return video_ids
                return video_ids
            elif count < 2:
                return await fetch_youtube_video(channel_id, count + 1)
            else:
                return None

async def check_youtube(channel_id):
    video_ids = await fetch_youtube_video(channel_id)
    if video_ids != None:
        for video_id in video_ids:
            if video_id in youtube_channels[channel_id]["video_id"]:
                if youtube_channels[channel_id]["video_id"][video_id] != video_ids[video_id]:
                    youtube_channels[channel_id]["video_id"][video_id] = video_ids[video_id]
            else:
                youtube_channels[channel_id]["video_id"][video_id] = video_ids[video_id]
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/data/youtube_channels.json", "w") as f : 
            json.dump(youtube_channels, f, indent=4)

async def loop_check():
    await asyncio.gather(*[check_youtube(channel_id) for channel_id in youtube_channels])

async def before_loop_check():
    global youtube_channels
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/data/youtube_channels.json", "r") as f:
        youtube_channels = json.load(f)

asyncio.run(before_loop_check())
asyncio.run(loop_check())