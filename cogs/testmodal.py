import discord
from discord.ext import commands
from commands import Context

class Test(commands.Cog, name='test'):
    def __init__(self, bot):
        self.bot = bot

    class TestModal(discord.ui.Modal, title="TestModal"):
        def __init__(self):
            pass
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

    class TestButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label="popupmodal")
        async def modalbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
            modal = self.TestModal()
            await interaction.response.send_modal(TestModal())

    @commands.hybrid_command(name="modaltest")
    async def test(self, ctx: Context):
        await ctx.send(view=TestButton())

async def setup(bot):
    await bot.add_cog(Test(bot))