from discord.ui import Modal, View
import discord
from discord.ext import commands

class Test(commands.Cog, name='test'):
    def __init__(self, bot):
        self.bot = bot

    class TestModal(Modal, View, title="TestModal"):
        name = discord.ui.TextInput(
            label="Name",
            placeholder="Your name here...",
        )
        answer = discord.ui.TextInput(
            label="Answer",
            placeholder="Your answer here...",
        )

        async def on_submit(self, context: commands.Context):
            await context.send(f"test\n{self.name}\n{self.answer}")

    @discord.app_commands.tree.CommandTree(name="modaltest")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.TestModal())

async def setup(bot):
    await bot.add_cog(Test(bot))