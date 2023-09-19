import discord
from discord import app_commands
import asyncio
from googleapiclient.discovery import build
import json
import feedparser
import aiohttp
from bs4 import BeautifulSoup
import DES2

#YOUTUBE_API_KEY = 'AIzaSyDX7P5Y3erIHvvP9zoPxwsravcpSgG0gcI'    #sinhouse2
YOUTUBE_API_KEY = 'AIzaSyB9n_pEu1dPbGxSN6dAgrfp-IqWelQ9q1o'     #sinhouse327

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
intents.reactions = True

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

discord_channel_id = 1133945327360168088


@client.event
async def on_ready():
    global youtube_channels         
    await tree.sync()
    with open("youtube_channels.json", "r") as f:
        youtube_channels = json.load(f)
    print(f'Logged in as {client.user.name} ({client.user.id})')
    print('------')
    await main()

async def send_new_video_link(video_id):
    video_url = f'https://youtu.be/{video_id}'
    channel = client.get_channel(discord_channel_id)
    await channel.send(video_url)

async def fetch_youtube_video(channel_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}') as response:
            if response.status == 200:
                data = await response.text()
                feed = await asyncio.to_thread(feedparser.parse, data)
                video_id = feed["entries"][0]["yt_videoid"]
                return video_id
            else:
                await fetch_youtube_video(channel_id)

async def check_youtube(channel_id):
    video_id = str(await fetch_youtube_video(channel_id))
    latest_video_id = youtube_channels[channel_id]["latest_video_id"]

    if latest_video_id is None:
        latest_video_id = video_id
        await send_new_video_link(video_id)
    elif latest_video_id != video_id:
        latest_video_id = video_id
        await send_new_video_link(video_id)

    youtube_channels[channel_id]["latest_video_id"] = latest_video_id

async def main():
    while True:
        await asyncio.gather(*[check_youtube(channel_id=channel_id) for channel_id in youtube_channels])
        await asyncio.sleep(60)


@tree.command(name='목록', description='알림을 받는 유튜브 채널 목록을 불러옵니다')
async def list(interaction: discord.Interaction):
    await interaction.response.defer()

    embeds = []

    async def make_embeds(channel_id):
        channel_name = youtube_channels[channel_id]["channel_name"]
        channel_description = youtube_channels[channel_id]["channel_description"]
        channel_image_url = youtube_channels[channel_id]["channel_image_url"]

        embed=discord.Embed(title="", url=f"https://www.youtube.com/channel/{channel_id}", description=channel_description, color=0xff0000)
        embed.set_author(name=channel_name, url=f"https://www.youtube.com/channel/{channel_id}", icon_url=channel_image_url)
        embed.set_thumbnail(url=channel_image_url)

        embeds.append(embed)

    await asyncio.gather(*[make_embeds(channel_id=channel_id) for channel_id in youtube_channels])
    await interaction.followup.send(content='', embeds=embeds)


@tree.command(name='추가', description='알림을 받을 유튜브 채널을 추가합니다')
@app_commands.describe(search='알림을 받을 유튜브 채널을 입력하세요')
async def add_channel(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

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

    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']

    sent_message = await interaction.channel.send(content='', embeds=embeds)

    async def add_reaction(reaction):
        await sent_message.add_reaction(reaction)

    await asyncio.gather(*[add_reaction(reaction) for reaction in reactions])

    
    @client.event
    async def on_reaction_add(reaction, user):
        if user.bot:
            return
        elif user == interaction.user and reaction.message == sent_message:
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
                        "channel_name": channel_names[selected_value],
                        "channel_image_url": channel_image_urls[selected_value],
                        "channel_description": channel_descriptions[selected_value]
                    }
                await interaction.followup.send("알림을 받을 유튜브 채널을 추가했습니다.", embed=embeds[selected_value])
                await sent_message.delete()
                await check_youtube(channel_id)
                return
        else:
            return


@tree.command(name='종료', description='봇을 종료합니다')
async def shutdown(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.id in [508138071984832513, 1021753759015116820]:
        with open("youtube_channels.json", "w") as f : 
            json.dump(youtube_channels, f, indent=4)
        await interaction.followup.send("봇을 종료합니다")
        await client.close()
    else:
        interaction.followup.send(f"너는 {client.user.mention}을(를) 종료할 권한이 없습니다.")


with open("bot.token","rb") as f:
    encrypted_token = f.read()
key = input("KEY를 입력해주세요: ")
token = DES2.new_(key).decrypt(encrypted_token).decode('utf-8')
client.run(token)