from typing import Any, Optional, Union
import discord
from discord import app_commands
from discord.emoji import Emoji
from discord.enums import ButtonStyle
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji
from googleapiclient.discovery import build
import aiohttp
import feedparser
import asyncio
import re
import os
import json
from dotenv import load_dotenv

load_dotenv()

youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))

class Youtube(commands.Cog, name="youtube"):
    def __init__(self, bot):
        self.bot = bot

    async def send_new_video_link(self, video_id):
        video_url = f'https://youtu.be/{video_id}'
        for notification_channel_id in notification_channels:
            notification_channel = await self.bot.fetch_channel(int(notification_channel_id))
            await notification_channel.send(video_url)

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
        video_id = await self.fetch_youtube_video(channel_id)
        latest_video_id = youtube_channels[channel_id]["latest_video_id"]
        second_video_id = youtube_channels[channel_id]["second_video_id"]

        if latest_video_id is None or (video_id not in [latest_video_id, second_video_id]):
            second_video_id = latest_video_id
            latest_video_id = video_id
            youtube_channels[channel_id]['latest_video_id'] = latest_video_id
            youtube_channels[channel_id]['second_video_id'] = second_video_id
            await self.send_new_video_link(video_id)
            with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "w") as f : 
                json.dump(youtube_channels, f, indent=4)

    @tasks.loop(minutes=1.0)
    async def loop_check(self):
        await asyncio.gather(*[self.check_youtube(channel_id) for channel_id in youtube_channels])

    @loop_check.before_loop
    async def before_loop_check(self):
        global youtube_channels, notification_channels
        with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "r") as f:
            youtube_channels = json.load(f)
        with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/notification_channels.json", "r") as f:
            notification_channels = json.load(f)

    async def cog_load(self):
        self.loop_check.start()

    @commands.hybrid_command(name="채널", description="새 영상 알림을 받을 디스코드 채널을 추가합니다")
    @app_commands.describe(channel_id="알림을 받을 디스코드 채널의 ID를 입력해주세요")
    async def add_discord_channel(self, context: Context, channel_id: str):
        notification_channels.append(channel_id)
        with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/notification_channels.json", "w") as f:
            json.dump(notification_channels, f, indent=4)
        await context.send("알림을 보낼 디스코드 채널을 추가했습니다", silent=True)

    @commands.hybrid_command(name='알림', description='알림을 받을 유튜브 채널을 추가합니다')
    @app_commands.describe(search='알림을 받을 유튜브 채널을 입력하세요')
    async def add_channel(self, context: Context, search: str):
        await context.defer()

        search_response = youtube.search().list(
        q=search,
        type='channel',
        part='snippet',
        maxResults=5
        ).execute()

        channel_names = []
        channel_image_urls = []
        channel_descriptions = []
        embeds = []

        for search_result in search_response.get("items", []):
            channel_id = search_result["id"]["channelId"]
            channel_name = search_result["snippet"]["title"]
            channel_description = search_result['snippet']['description']
            channel_image_url = search_result["snippet"]["thumbnails"]["default"]["url"]

            embed=discord.Embed(title="", url=f"https://www.youtube.com/channel/{channel_id}", description=channel_description, color=0xff0000)
            embed.set_author(name=channel_name, url=f"https://www.youtube.com/channel/{channel_id}", icon_url=channel_image_url)
            embed.set_thumbnail(url=channel_image_url)

            channel_names.append(channel_name)
            channel_image_urls.append(channel_image_url)
            channel_descriptions.append(channel_description)
            embeds.append(embed)

        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '❎']

        sent_message = await context.channel.send(content='', embeds=embeds)

        async def add_reaction(reaction):
            await sent_message.add_reaction(reaction)

        await asyncio.gather(*[add_reaction(reaction) for reaction in reactions])

        @self.bot.event
        async def on_reaction_add(reaction, user):

            if user.bot:
                return
            if user == context.author and reaction.message == sent_message:
                emoji_to_value = {
                    '1️⃣': 0,
                    '2️⃣': 1,
                    '3️⃣': 2,
                    '4️⃣': 3,
                    '5️⃣': 4
                }

                if reaction.emoji in emoji_to_value:
                    selected_value = emoji_to_value[reaction.emoji]
                    channel = search_response.get("items", [])[selected_value]
                    channel_id = str(channel['id']['channelId'])
                    if channel_id not in youtube_channels:
                        youtube_channels[channel_id] = {
                            "latest_video_id": None,
                            "second_video_id": None,
                            "channel_name": channel_names[selected_value],
                            "channel_image_url": channel_image_urls[selected_value],
                            "channel_description": channel_descriptions[selected_value]
                        }
                        await sent_message.delete()
                        await context.send("알림을 받을 유튜브 채널을 추가했습니다.", embed=embeds[selected_value])
                        await self.check_youtube(channel_id)
                    else:
                        await sent_message.delete()
                        await context.send("이미 추가된 채널입니다")
                if reaction.emoji == '❎':
                    await sent_message.delete()
                    await context.send("채널 추가를 취소합니다")

    @commands.hybrid_command(name="목록", description="유튜브 채널 목록을 불러옵니다")
    async def channel_list(self, context: Context):
        await context.send("유튜브 채널 목록을 불러옵니다", delete_after=180)

        async def send_list(channel_id):
            channel_name = youtube_channels[channel_id]["channel_name"]
            channel_description = youtube_channels[channel_id]["channel_description"]
            channel_image_url = youtube_channels[channel_id]["channel_image_url"]

            embed=discord.Embed(title="", url=f"https://www.youtube.com/channel/{channel_id}", description=channel_description, color=0xff0000)
            embed.set_author(name=channel_name, url=f"https://www.youtube.com/channel/{channel_id}", icon_url=channel_image_url)
            embed.set_thumbnail(url=channel_image_url)

            view = discord.ui.View()
            button1 = VideoButton(custom_id=f"vid_{channel_id}", emoji="✅")
            button2 = DeleteButton(custom_id=f"del_{channel_id}", emoji="❎")
            view.add_item(button1)
            view.add_item(button2)

            await context.channel.send(embed=embed, view=view, silent=True, delete_after=180)

        await asyncio.gather(*[send_list(channel_id=channel_id) for channel_id in youtube_channels])

class DeleteButton(discord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.red, label = "채널삭제", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)

    async def callback(self, interaction) -> Any:
        if interaction.user not in [628120124464955392, 1024995328124014673]:
            message = interaction.message
            await message.delete()
            del youtube_channels[re.search(r"del_(.*)", self.custom_id).group(1)]
            with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "w") as f:
                json.dump(youtube_channels, f, indent=4)
        else:
            await interaction.response.send_message("쪼또'만' 메시지를 삭제할 권한이 없습니다")

class VideoButton(discord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.primary, label = "최신영상", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)

    async def callback(self, interaction) -> Any:
        channel_id = re.search(r"vid_(.*)", self.custom_id).group(1)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}') as response:
                if response.status == 200:
                    data = await response.text()
                    feed = await asyncio.to_thread(feedparser.parse, data)

        global embeds
        embeds = []

        for video in feed["entries"]:
            channel_name = video["author_detail"]["name"]
            channel_url = video["author_detail"]["href"]
            channel_icon_url = youtube_channels[channel_id]["channel_image_url"]
            video_title = video["title"]
            video_url = video["link"]
            video_thumbnail_url = video["media_thumbnail"][0]["url"]

            embed = discord.Embed(
                title=video_title,
                url=video_url,
                color=0xff0000
            )
            embed.set_image(
                url=video_thumbnail_url,
            )
            embed.set_author(
                name=channel_name,
                url=channel_url,
                icon_url=channel_icon_url
            )
            embeds.append(embed)

        max_page = len(embeds)
        page = 0
        prev_button = PrevButton(page, max_page, disabled=True)
        next_button = NextButton(page, max_page)
        view = discord.ui.View()
        view.add_item(prev_button)
        view.add_item(next_button)
        await interaction.response.send_message(embed=embeds[page], view=view)

class PrevButton(discord.ui.Button):
    def __init__(self, page, max_page, *, style: ButtonStyle = ButtonStyle.secondary, label = "Prev", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji = "⬅️", row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.page = page
        self.max_page = max_page

    async def callback(self, interaction: discord.Interaction) -> Any:
        self.page = self.page - 1
        if self.page > 0:
            prev_button = PrevButton(self.page, self.max_page)
        else:
            prev_button = PrevButton(self.page, self.max_page, disabled=True)
        next_button = NextButton(self.page, self.max_page)
        view = discord.ui.View()
        view.add_item(prev_button)
        view.add_item(next_button)
        await interaction.response.edit_message(embed=embeds[self.page], view=view)

class NextButton(discord.ui.Button):
    def __init__(self, page, max_page, *, style: ButtonStyle = ButtonStyle.secondary, label = "Next", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji = "➡️", row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.page = page
        self.max_page = max_page - 1

    async def callback(self, interaction: discord.Interaction) -> Any:
        self.page = self.page + 1
        if self.page < self.max_page:
            next_button = NextButton(self.page, self.max_page)
        else:
            next_button = NextButton(self.page, self.max_page,disabled=True)
        prev_button = PrevButton(self.page, self.max_page)
        view = discord.ui.View()
        view.add_item(prev_button)
        view.add_item(next_button)
        await interaction.response.edit_message(embed=embeds[self.page], view=view)

async def setup(bot):
    await bot.add_cog(Youtube(bot))