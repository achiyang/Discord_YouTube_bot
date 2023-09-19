import discord
from discord.ext import commands
import getpass
import DES2

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=">>>", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()

@bot.tree.command(name="test", description='command trre test')
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("test")

if __name__ == "__main__":
    with open("youtube.bot/bot.token","rb") as f:
        encrypted_token = f.read()
    key = getpass.getpass("KEY를 입력해주세요: ")
    token = DES2.new(key).decrypt(encrypted_token).decode('utf-8')
    bot.run(token)