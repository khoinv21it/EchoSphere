import discord
from discord.ext import commands

class ResumeCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='resume')
    async def resume_cmd(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state or not state.voice_client:
            return await ctx.reply('Not connected')
        if state.voice_client.is_paused():
            state.voice_client.resume()
            await ctx.reply('Resumed')


async def setup(bot: commands.Bot):
    await bot.add_cog(ResumeCommand(bot))
