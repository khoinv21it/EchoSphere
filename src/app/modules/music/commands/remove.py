import discord
from discord.ext import commands

class RemoveCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='remove')
    async def remove_cmd(self, ctx: commands.Context, index: int):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state:
            return await ctx.reply('Nothing to remove')
        removed = state.queue.remove_at(index-1)
        if not removed:
            return await ctx.reply('Invalid index')
        await ctx.reply(f'Removed: {removed.title}')


async def setup(bot: commands.Bot):
    await bot.add_cog(RemoveCommand(bot))
