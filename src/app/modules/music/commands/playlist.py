from discord.ext import commands
from app.services.session import ensure_guild_state, connect_voice
from app.services.player import ytdl_info, Track as TrackClass, play_next

class PlaylistCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='playlist')
    async def playlist_cmd(self, ctx: commands.Context, *, url: str):
        state = await ensure_guild_state(ctx.guild)
        info = await ytdl_info(url)
        if not info or info.get('_type') != 'playlist':
            return await ctx.reply('Failed to parse playlist or not a playlist')
        count = 0
        for item in info.get('entries', []):
            track = TrackClass(title=item.get('title'), url=item.get('webpage_url'), duration=int(item.get('duration') or 0), requested_by=ctx.author.display_name, thumbnail=item.get('thumbnail'))
            state.queue.enqueue(track)
            count += 1
        if not state.voice_client or not state.voice_client.is_connected():
            if ctx.author.voice and ctx.author.voice.channel:
                await connect_voice(state, ctx.author.voice.channel)
        if not state.current_track:
            await play_next(self.bot, state, ctx.guild.id)
        await ctx.reply(f'Enqueued {count} tracks from playlist')

    @commands.command(name='playlist')
    async def playlist_cmd(self, ctx: commands.Context, *, name: str = None):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        # placeholder: just show queue
        if not state or state.queue.length==0:
            try:
                return await ctx.reply('No playlist or queue is empty')
            except Exception:
                return await ctx.reply('No playlist or queue is empty')
        lines = [f"{i+1}. {t.title} — {t.requested_by or 'Unknown'}" for i,t in enumerate(state.queue.list)]
        try:
            from app.utils.discord.helpers import send_unique
            await send_unique(ctx.channel, content='\n'.join(lines[:50]))
        except Exception:
            await ctx.reply('\n'.join(lines[:50]))


async def setup(bot: commands.Bot):
    await bot.add_cog(PlaylistCommand(bot))
