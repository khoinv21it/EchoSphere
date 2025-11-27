import discord
from discord.ext import commands

class StopCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='stop')
    async def stop_cmd(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state or not state.voice_client:
            return await ctx.reply('Not connected')
        state.queue.clear()
        state.voice_client.stop()
        await state.voice_client.disconnect()
        state.voice_client = None
        await ctx.reply('Stopped and disconnected')


async def setup(bot: commands.Bot):
    await bot.add_cog(StopCommand(bot))
