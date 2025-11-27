import discord
from discord.ext import commands

class NowPlayingCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='nowplaying')
    async def nowplaying(self, ctx: commands.Context):
        from app.services.session import guild_states
        state = guild_states.get(ctx.guild.id)
        if not state or not state.current_track:
            return await ctx.reply('Nothing is playing')
        track = state.current_track
        embed = discord.Embed(title='Now Playing', description=f'**{track.title}**', color=0x1DB954)
        embed.add_field(name='Requested By', value=track.requested_by or 'Unknown', inline=True)
        embed.add_field(name='Duration', value=f'{track.duration}s', inline=True)
        if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(NowPlayingCommand(bot))
