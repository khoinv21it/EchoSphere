import discord
from discord.ext import commands

class PauseCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='pause')
    async def pause_cmd(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        state.last_text_channel = ctx.channel
        if not state or not state.voice_client:
            return await ctx.reply('Not connected')
        if state.voice_client.is_playing():
            state.voice_client.pause()
            await ctx.reply('Paused')


async def setup(bot: commands.Bot):
    await bot.add_cog(PauseCommand(bot))
