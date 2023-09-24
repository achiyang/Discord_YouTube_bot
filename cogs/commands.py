from discord.ext import commands
from discord.ext.commands import Context

class Commands(commands.Cog, name='commands'):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, context: Context) -> bool:
        if context.author.id not in [508138071984832513, 1021753759015116820]:
            await context.send("이 명령어를 사용할 권한이 없습니다")
            return False
        else:
            return True

    @commands.hybrid_command(name="업데이트", description="봇을 업데이트합니다")
    async def update(self, context: Context):
        await self.bot.reload_cogs()
        await self.bot.tree.sync()
        await context.send("봇 업데이트를 완료했습니다", ephemeral=True)

    @commands.hybrid_command(name="종료", description="봇을 종료합니다")
    async def shutdown(self, context: Context):
        await context.send("봇을 종료했습니다", ephemeral=True)
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Commands(bot))