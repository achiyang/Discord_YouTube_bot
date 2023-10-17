import aiohttp
import asyncio
import feedparser

async def fetch_youtube_video(channel_id, count: int | None = 0) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}', allow_redirects=True) as response:
            if response.status == 200:
                video_ids = {}
                data = await response.text()
                feed = await asyncio.to_thread(feedparser.parse, data)
                for i in range(len(feed["entries"])):
                    video_id = feed["entries"][i]["yt_videoid"]
                    published = feed["entries"][i]["published"]
                    if "updated" in feed["entries"][i]:
                        updated = feed["entries"][i]["updated"]
                    else:
                        updated = ""
                    views = feed["entries"][i]["media_statistics"]["views"]
                    video_ids[video_id] = {
                        "published": published,
                        "updated": updated,
                        "views": views
                    }
                return video_ids
            elif count < 2:
                return await fetch_youtube_video(channel_id, count + 1)
            else:
                return None
            
async def test():
    videos = await fetch_youtube_video("UCJFZiqLMntJufDCHc6bQixg")
    print(videos)

asyncio.run(test())