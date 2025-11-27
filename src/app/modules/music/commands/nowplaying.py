from discord.ext import commands
from app.utils.discord.helpers import make_now_playing_embed, send_unique

class NowPlayingCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='nowplaying', aliases=['np'])
    async def nowplaying(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)

        # remember where to send now-playing updates
        if state is not None:
            state.last_text_channel = ctx.channel

        # If nothing is playing and voice client not active, send a single unique message
        if not state or (not state.current_track and not (getattr(state, 'voice_client', None) and getattr(state.voice_client, 'is_playing', lambda: False)())):
            return await send_unique(ctx.channel, content='Nothing is playing')

        # If current_track missing but voice client is playing, try to recover from history
        if not state.current_track and getattr(state, 'voice_client', None) and getattr(state.voice_client, 'is_playing', lambda: False)():
            try:
                hist = getattr(state, 'history', None) or []
                if hist:
                    # assume most recent history item is the current (best-effort)
                    candidate = hist[0]
                    state.current_track = candidate
                else:
                    # try to inspect now_playing_message embed
                    npm = getattr(state, 'now_playing_message', None)
                    if npm and getattr(npm, 'embeds', None):
                        emb = npm.embeds[0]
                        # create a minimal Track-like object for display
                        class _T:
                            pass
                        t = _T()
                        t.title = getattr(emb, 'title', 'Unknown') or 'Unknown'
                        t.requested_by = 'Unknown'
                        t.duration = 0
                        state.current_track = t
            except Exception:
                pass

        # If we have metadata, send embed (use send_unique to avoid duplicate embeds)
        if state.current_track:
            embed = make_now_playing_embed(state.current_track)
            try:
                await send_unique(ctx.channel, embed=embed)
            except Exception:
                await ctx.reply(embed=embed)
            return

        # Voice client is playing but metadata unavailable
        await send_unique(ctx.channel, content='Audio is playing, but metadata is unavailable')


async def setup(bot: commands.Bot):
    await bot.add_cog(NowPlayingCommand(bot))
