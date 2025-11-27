import discord
from discord.ext import commands

class LoopCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='loop')
    async def loop_cmd(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        state.queue.loop = not state.queue.loop
        await ctx.reply(f'Loop is now {state.queue.loop}')


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopCommand(bot))
