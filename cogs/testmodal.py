from discord.ui import Modal
import discord
from discord.ext import commands
from commands import Context

class Test(commands.Cog, name='test'):
    def __init__(self, bot):
        self.bot = bot

    class TestModal(Modal, title="TestModal"):
        name = discord.ui.TextInput(
            label="Name",
            placeholder="Your name here...",
        )
        answer = discord.ui.TextInput(
            label="Answer",
            placeholder="Your answer here...",
        )

        async def on_submit(self, ctx: Context):
            await ctx.send(f"test\n{self.name}\n{self.answer}")

    @commands.hybrid_command(name="modaltest")
    async def test(self, ctx: Context):
        await ctx.send(self.TestModal())

async def setup(bot):
    await bot.add_cog(Test(bot))