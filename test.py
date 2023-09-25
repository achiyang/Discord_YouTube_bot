import feedparser
import aiohttp
import json
import asyncio

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.youtube.com/feeds/videos.xml?channel_id=UCXTpFs_3PqI41qX2d9tL2Rw') as response:
            if response.status == 200:
                data = await response.text()
                feed = feedparser.parse(data)
                with open("test.json", "w") as f:
                    json.dump(feed, f, indent=4)

if __name__ == "__main__":
    asyncio.run(test())