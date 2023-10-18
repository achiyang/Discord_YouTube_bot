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
from collections import Counter
import asyncio
import aiohttp
import feedparser
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
        notification_channel_id = 1133945327360168088
        notification_channel = await self.bot.fetch_channel(notification_channel_id)
        await notification_channel.send(video_url)

    async def fetch_youtube_video(self, channel_id, count: int | None = 0) -> dict | None:
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
                    return await self.fetch_youtube_video(channel_id, count + 1)
                else:
                    return None

    async def check_youtube(self, channel_id):
        video_ids = await self.fetch_youtube_video(channel_id)
        if video_ids != None:
            for video_id in video_ids:
                if video_id not in youtube_channels[channel_id]["video_id"]:
                    await self.send_new_video_link(video_id)
                else:
                    if youtube_channels[channel_id]["video_id"][video_id]["views"] == "0":
                        if video_ids[video_id]["views"] != "0":
                            await self.send_new_video_link(video_id)
                    else:
                        if video_ids[video_id]["views"] == "0":
                            video_ids[video_id]["views"] = ""
                youtube_channels[channel_id]["video_id"] = {video_id: video_ids[video_id], **youtube_channels[channel_id]["video_id"]}
            with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "w") as f : 
                json.dump(youtube_channels, f, indent=4)

    @tasks.loop(minutes=1.0)
    async def loop_check(self):
        await asyncio.gather(*[self.check_youtube(channel_id) for channel_id in youtube_channels])

    @loop_check.before_loop
    async def before_loop_check(self):
        global youtube_channels
        with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "r") as f:
            youtube_channels = json.load(f)
        tasks = [self.sort_video_id(channel_id) for channel_id in youtube_channels]
        asyncio.gather(*tasks)

    async def cog_load(self):
        self.loop_check.start()

    async def sort_video_id(self, channel_id):
        sorted_video_id = dict(
            sorted(
                youtube_channels[channel_id]["video_id"].items(),
                key=lambda item: item[1]["published"]
            )
        )
        youtube_channels[channel_id]["video_id"] = sorted_video_id

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
                        video_id = await self.fetch_youtube_video(channel_id)
                        youtube_channels[channel_id] = {
                            "channel_name": channel_names[selected_value],
                            "channel_image_url": channel_image_urls[selected_value],
                            "channel_description": channel_descriptions[selected_value],
                            "video_id": video_id if video_id != None else {}
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
        global chunked_channels
        chunked_channels = [list(youtube_channels.keys())[i:i + 5] for i in range(0, len(youtube_channels), 5)]

        current_page = 0

        msg = await context.send(content=f"유튜브 채널 목록을 불러옵니다 (페이지 {current_page + 1}/{len(chunked_channels)})",view=None,silent=True)

        global messages
        messages = []

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

            messages.append(await context.channel.send(embed=embed, view=view, silent=True))

        for channel_id in chunked_channels[current_page]:
            await send_list(channel_id)

        view = discord.ui.View()
        prev_button = PageButton(msg, current_page, "Prev", is_next=False, emoji="⬅️", disabled=True)
        next_button = PageButton(msg, current_page, "Next", is_next=True, emoji="➡️")
        delete_button = DeletePageButton(msg=msg)
        view.add_item(prev_button)
        view.add_item(next_button)
        view.add_item(delete_button)
        await context.channel.send(view=view, silent=True)

class PageButton(discord.ui.Button):
    def __init__(self, msg, page, label, is_next, *, style: ButtonStyle = ButtonStyle.secondary, disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.page = page
        self.is_next = is_next
        self.msg = msg
        if is_next:
            self.emoji = "➡️"
        else:
            self.emoji = "⬅️"

    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.is_next:
            self.page = self.page + 1
        else:
            self.page = self.page - 1

        await self.msg.edit(content=f"유튜브 채널 목록을 불러옵니다 (페이지 {self.page + 1}/{len(chunked_channels)})", view=None)

        if self.is_next and self.page < len(chunked_channels) - 1:
            next_button = PageButton(self.msg, self.page, "Next", is_next=True)
        elif self.is_next:
            next_button = PageButton(self.msg, self.page, "Next", is_next=True, disabled=True)
        elif not self.is_next and self.page > 0:
            prev_button = PageButton(self.msg, self.page, "Prev", is_next=False)
        else:
            prev_button = PageButton(self.msg, self.page, "Prev", is_next=False, disabled=True)

        view = discord.ui.View()
        if self.is_next:
            prev_button = PageButton(self.msg, self.page, "Prev", is_next=False)
        elif not self.is_next:
            next_button = PageButton(self.msg, self.page, "Next", is_next=True)
        delete_button = DeletePageButton(msg=self.msg)
        view.add_item(prev_button)
        view.add_item(next_button)
        view.add_item(delete_button)
        await interaction.response.edit_message(content=None,view=view)

        async def edit_list(i, channel_id):
            if channel_id in youtube_channels:
                channel_name = youtube_channels[channel_id]["channel_name"]
                channel_description = youtube_channels[channel_id]["channel_description"]
                channel_image_url = youtube_channels[channel_id]["channel_image_url"]

                embed = discord.Embed(
                    title="",
                    url=f"https://www.youtube.com/channel/{channel_id}",
                    description=channel_description,
                    color=0xff0000
                )
                embed.set_author(
                    name=channel_name,
                    url=f"https://www.youtube.com/channel/{channel_id}",
                    icon_url=channel_image_url
                )
                embed.set_thumbnail(url=channel_image_url)

                view = discord.ui.View()
                button1 = VideoButton(custom_id=f"vid_{channel_id}", emoji="✅")
                button2 = DeleteButton(custom_id=f"del_{channel_id}", emoji="❎")
                view.add_item(button1)
                view.add_item(button2)

                await messages[i].edit(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    description="삭제되었습니다",
                    color=0xff0000
                )
                await messages[i].edit(embed=embed, view=None)

        empty_embed = discord.Embed(
            description="비어있습니다",
            color=0xff0000
        )

        len_ = len(chunked_channels[self.page])
        if len_ < 5:
            for i in range(5 - len_):
                await messages[len_ + i].edit(content=None, embed=empty_embed, view=None)

        await asyncio.gather(*[edit_list(i, channel_id) for i, channel_id in enumerate(chunked_channels[self.page])])

class DeletePageButton(discord.ui.Button):
    def __init__(self, msg, *, style: ButtonStyle = ButtonStyle.red, label = "X", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.msg = msg

    async def callback(self, interaction: Interaction) -> Any:
        await interaction.message.delete()
        await self.msg.delete()
        await asyncio.gather(*[msg.delete() for msg in messages])

class DeleteButton(discord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.red, label = "채널삭제", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)

    async def callback(self, interaction) -> Any:
        if interaction.user.id in [508138071984832513, 1021753759015116820]:
            deleted_embed = discord.Embed(
                description="삭제되었습니다",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=deleted_embed, view=None)
            del youtube_channels[re.search(r"del_(.*)", self.custom_id).group(1)]
            with open(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/data/youtube_channels.json", "w") as f:
                json.dump(youtube_channels, f, indent=4)
        else:
            await interaction.response.send_message("채널 삭제 권한은 아치양에게만 있습니다", ephemeral=True)

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
            video_thumbnail_url = video["media_thumbnail"][0]["url"].replace("hqdefault", "maxresdefault")

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
        prev_button = VideopnButton(page, max_page, is_prev=True, label="Prev", emoji="⬅️", disabled=True)
        next_button = VideopnButton(page, max_page, is_prev=False, label="Next", emoji="➡️")
        del_button = DeleteVideoButton()
        view = discord.ui.View()
        view.add_item(prev_button)
        view.add_item(next_button)
        view.add_item(del_button)
        await interaction.response.send_message(content=f"{page+1}/{max_page}" ,embed=embeds[page], view=view, silent=True)

class VideopnButton(discord.ui.Button):
    def __init__(self, page, max_page, is_prev: bool, *, style: ButtonStyle = ButtonStyle.secondary, label: str | None = None, disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.page = page
        self.max_page = max_page
        self.is_prev = is_prev
        if is_prev:
            self.emoji = "⬅️"
        else:
            self.emoji = "➡️"

    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.is_prev:
            self.page = self.page - 1
        else:
            self.page = self.page + 1

        if self.is_prev and self.page > 0:
            prev_button = VideopnButton(self.page, self.max_page, is_prev=True, label="Prev")
        elif self.is_prev:
            prev_button = VideopnButton(self.page, self.max_page, is_prev=True, label="Prev", disabled=True)
        elif not self.is_prev and self.page < self.max_page - 1:
            next_button = VideopnButton(self.page, self.max_page, is_prev=False, label="Next")
        else:
            next_button = VideopnButton(self.page, self.max_page, is_prev=False, label="Next", disabled=True)

        if self.is_prev:
            next_button = VideopnButton(self.page, self.max_page, is_prev=False, label="Next")
        else:
            prev_button = VideopnButton(self.page, self.max_page, is_prev=True, label="Prev")

        del_button = DeleteVideoButton()
        view = discord.ui.View()
        view.add_item(prev_button)
        view.add_item(next_button)
        view.add_item(del_button)
        await interaction.response.edit_message(content=f"{self.page+1}/{self.max_page}" ,embed=embeds[self.page], view=view)

class DeleteVideoButton(discord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.red, label = "X", disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> Any:
        await interaction.message.delete()

async def setup(bot):
    await bot.add_cog(Youtube(bot))