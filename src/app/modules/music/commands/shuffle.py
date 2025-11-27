import discord
from discord.ext import commands

class ShuffleCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='shuffle')
    async def shuffle(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state:
            return await ctx.reply('Nothing to shuffle')
        state.queue.shuffle()
        await ctx.reply('Shuffled the queue')


async def setup(bot: commands.Bot):
    await bot.add_cog(ShuffleCommand(bot))
