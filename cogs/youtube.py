import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
import aiohttp
import asyncio
import os
import json

class Youtube(commands.Cog, name="youtube"):
    def __init__(self, bot):
        self.bot = bot

    async def send_new_video_link(self, video_id):
        video_url = f'https://youtu.be/{video_id}'
        channel = client.get_channel(discord_channel_id)
        await channel.send(video_url)

    async def fetch_youtube_video(self, channel_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}') as response:
                if response.status == 200:
                    data = await response.text()
                    feed = await asyncio.to_thread(feedparser.parse, data)
                    video_id = feed["entries"][0]["yt_videoid"]
                    return video_id
                else:
                    await self.fetch_youtube_video(channel_id)

    async def check_youtube(self, channel_id):
        change = False
        video_id = str(await self.fetch_youtube_video(channel_id))
        latest_video_id = youtube_channels.get(channel_id).get("latest_video_id")

        if latest_video_id is None or latest_video_id != video_id:
            latest_video_id = video_id
            await self.send_new_video_link(video_id)
            change = True

        if change:
            youtube_channels[channel_id]["latest_video_id"] = latest_video_id
            with open("youtube_channels.json", "w") as f : 
                json.dump(youtube_channels, f, indent=4)

    @tasks.loop(minutes=1)
    async def loop_check(self):
        await asyncio.gather(*[self.check_youtube(channel_id) for channel_id in youtube_channels])

    @loop_check.before_loop()
    async def before_loop_check(self):
        global youtube_channels
        with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "r") as f:
            youtube_channels = json.load(f)

async def setup(bot):
    await bot.add_cog(Youtube(bot))