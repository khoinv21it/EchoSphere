# This module will be a simplified version of play command — used by both prefix and slash
from discord.ext import commands
import discord
from app.services.player import ytdl_search, ytdl_info, Track as TrackClass
from app.services.session import ensure_guild_state, connect_voice, update_now_playing_message

async def enqueue_and_play(bot: commands.Bot, ctx_or_interaction, requester: discord.Member, query: str):
    # logic: resolve query to track and enqueue
    if query.startswith('https://open.spotify.com'):
        # simplification: use ytdl search to find youtube result
        pass
    if query.startswith('http'):
        info = await ytdl_info(query)
        if not info:
            return None, None
        item = TrackClass(title=info.get('title', 'Unknown'), url=info.get('webpage_url', query), duration=int(info.get('duration', 0)), requested_by=requester.display_name)
    else:
        results = await ytdl_search(query, 5)
        if not results:
            return None, None
        # present search results
        item = results[0]

    from app.services.session import ensure_guild_state, connect_voice
    state = await ensure_guild_state(requester.guild)
    state.queue.enqueue(item)
    # connect if not connected
    if not state.voice_client or not state.voice_client.is_connected():
        if requester.voice and requester.voice.channel:
            await connect_voice(state, requester.voice.channel)
    if not state.current_track:
        from app.services.player import play_next
        await play_next(bot, state, requester.guild.id)
    return state, item


class Play(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='play', aliases=['p', 'pl'])
    async def play(self, ctx, *, query: str):
        state, item = await enqueue_and_play(self.bot, ctx, ctx.author, query)
        if item:
            await ctx.reply(f'Enqueued: {item.title}')


async def setup(bot: commands.Bot):
    await bot.add_cog(Play(bot))
