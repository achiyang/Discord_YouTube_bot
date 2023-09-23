from discord.ext import commands
from discord.ext.commands import Context

class Commands(commands.Cog, name='commands'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="업데이트", description="봇을 업데이트합니다")
    async def update(self, context: Context):
        if context.author.id in [508138071984832513, 1021753759015116820]:
            await self.bot.reload_cogs()
            await self.bot.tree.sync()
            await context.send("봇 업데이트를 완료했습니다", ephemeral=True)

    @commands.hybrid_command(name="종료", description="봇을 종료합니다")
    async def shutdown(self, context: Context):
        if context.author.id in [508138071984832513, 1021753759015116820]:
            await context.send("봇을 종료했습니다", ephemeral=True)
            await self.bot.close()

async def setup(bot):
    await bot.add_cog(Commands(bot))