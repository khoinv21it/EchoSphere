import discord
from discord.ext import commands

class JoinCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='join')
    async def join_cmd(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.reply('You must join a voice channel first')
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state:
            # ensure_guild_state will create as needed; this should not happen
            state = await ensure_guild_state(ctx.guild)
        await ctx.author.voice.channel.connect()
        await ctx.reply(f'Joined {ctx.author.voice.channel.name}')


async def setup(bot: commands.Bot):
    await bot.add_cog(JoinCommand(bot))
