import discord
from discord import app_commands
from discord import ui
import sys
import os
from DES2.DES2 import new_
from getpass import getpass

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client=client)
intents.message_content = True

@client.event
async def on_ready():
    await tree.sync()
    print("ready")

class TestModal(ui.Modal, ui.View, title="TestModal"):
    name = ui.TextInput(
        label="Name",
        placeholder="Your name here...",
    )
    answer = ui.TextInput(
        label="Answer",
        placeholder="Your answer here...",
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"test\n{self.name}\n{self.answer}")

@tree.command(name="modaltest")
async def test(interaction: discord.Interaction):
    await interaction.response.send_modal(TestModal())

if len(sys.argv) > 1:
    key = sys.argv[1]
else:
    key = getpass("KEY를 입력해주세요: ")

encrypted_token = open(f"{os.path.realpath(os.path.dirname(__file__))}/bot.token", "rb").read()
bot_token = new_(key).decrypt(encrypted_token).decode('utf-8')

client.run(bot_token)
