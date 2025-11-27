import discord
from discord.ext import commands
from typing import Optional

class VolumeCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='volume')
    async def volume_cmd(self, ctx: commands.Context, percent: Optional[int] = None):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state:
            return await ctx.reply('No music session')
        if percent is None:
            return await ctx.reply(f'Volume: {int((getattr(state, "volume", 0.8) or 0.8) * 100)}%')
        p = max(0, min(100, percent))
        state.volume = p / 100.0
        await ctx.reply(f'Volume set to {p}%')


async def setup(bot: commands.Bot):
    await bot.add_cog(VolumeCommand(bot))
