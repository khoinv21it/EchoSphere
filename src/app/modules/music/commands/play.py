# This module will be a simplified version of play command — used by both prefix and slash
from discord.ext import commands
import discord
from app.services.player import ytdl_search, ytdl_info, Track as TrackClass
import asyncio

# per-guild lock to serialize enqueue operations and avoid races
_guild_locks = {}

async def enqueue_and_play(bot: commands.Bot, ctx_or_interaction, requester: discord.Member, query: str):
    # resolve query to one or more Track items (handle playlists)
    items = []
    try:
        if 'list=' in query or 'playlist' in query:
            # likely a playlist URL — try to extract entries
            info = await ytdl_info(query)
            if info and isinstance(info, dict):
                entries = info.get('entries') or []
                for e in entries:
                    if not e: continue
                    items.append(TrackClass(title=e.get('title'), url=e.get('webpage_url'), duration=int(e.get('duration') or 0), requested_by=requester.display_name))
        else:
            # not a playlist: single track resolution
            if query.startswith('http'):
                info = await ytdl_info(query)
                if not info:
                    return None, None
                items.append(TrackClass(title=info.get('title', 'Unknown'), url=info.get('webpage_url', query), duration=int(info.get('duration', 0)), requested_by=requester.display_name))
            else:
                results = await ytdl_search(query, 5)
                if not results:
                    return None, None
                items.append(results[0])
    except Exception:
        return None, None

    # acquire per-guild lock before mutating state
    lock = _guild_locks.setdefault(requester.guild.id, asyncio.Lock())
    async with lock:
        from app.services.session import ensure_guild_state, connect_voice
        state = await ensure_guild_state(requester.guild)
        # remember where to send now-playing updates
        state.last_text_channel = ctx_or_interaction.channel if hasattr(ctx_or_interaction, 'channel') else None

        enqueued_any = []
        for item in items:
            # dedupe per item
            try:
                dup = False
                if getattr(state, 'current_track', None) and getattr(state.current_track, 'url', None) == item.url:
                    dup = True
                for t in state.queue.list:
                    if getattr(t, 'url', None) == item.url:
                        dup = True
                        break
                if dup:
                    # notify user that this specific track is duplicate
                    try:
                        if hasattr(ctx_or_interaction, 'reply'):
                            await ctx_or_interaction.reply(f'Track already in queue: {item.title}')
                        elif state.last_text_channel:
                            await state.last_text_channel.send(f'Track already in queue: {item.title}')
                    except Exception:
                        pass
                    continue
            except Exception:
                pass
            state.queue.enqueue(item)
            enqueued_any.append(item)

        if not enqueued_any:
            return None, None

        # connect if not connected
        if not state.voice_client or not getattr(state.voice_client, 'is_connected', lambda: False)():
            if requester.voice and requester.voice.channel:
                await connect_voice(state, requester.voice.channel)
                # wait for voice handshake to complete before attempting playback
                connected = False
                for _ in range(25):  # up to ~2.5s
                    try:
                        if state.voice_client and getattr(state.voice_client, 'is_connected', lambda: False)():
                            connected = True
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.1)
                if not connected:
                    # inform user and abort enqueue-play flow
                    try:
                        if hasattr(ctx_or_interaction, 'reply'):
                            await ctx_or_interaction.reply('Failed to connect to voice channel. Please try again.')
                        elif state.last_text_channel:
                            await state.last_text_channel.send('Failed to connect to voice channel. Please try again.')
                    except Exception:
                        pass
                    # remove the enqueued items we just added
                    try:
                        for _ in enqueued_any:
                            # remove last occurrence
                            if state.queue.list and state.queue.list[-1].url == _.url:
                                state.queue.pop_last()
                    except Exception:
                        pass
                    return None, None

        # if nothing is currently playing, start playback
        if not state.current_track:
            from app.services.player import play_next
            await play_next(bot, state, requester.guild.id)
        else:
            # refresh now-playing UI so users see controls
            try:
                from app.services.session import update_now_playing_message
                await update_now_playing_message(bot, state)
            except Exception:
                pass

    # return state and the first enqueued item for user feedback
    return state, enqueued_any[0]


class Play(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='play', aliases=['p', 'pl'])
    async def play(self, ctx, *, query: str):
        state, item = await enqueue_and_play(self.bot, ctx, ctx.author, query)
        if item:
            # avoid duplicate full messages: react to user's message as acknowledgement
            try:
                await ctx.message.add_reaction('✅')
            except Exception:
                try:
                    await ctx.reply(f'Enqueued: {item.title}')
                except Exception:
                    pass

            # send a small UI to allow viewing the queue (one-time view)
            try:
                from app.utils.discord.helpers import send_unique
                class QueueButton(discord.ui.View):
                    def __init__(self, state):
                        super().__init__(timeout=60)
                        self.state = state

                    @discord.ui.button(label='📜 Queue', style=discord.ButtonStyle.secondary)
                    async def show_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
                        try:
                            from app.utils.discord.helpers import make_queue_embed
                            embed = make_queue_embed(self.state.queue, now_playing=self.state.current_track)
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        except Exception:
                            await interaction.response.send_message('Failed to show queue', ephemeral=True)

                # try to send a concise UI message (use send_unique to avoid duplicates)
                try:
                    await ctx.channel.send(content=f'Enqueued: {item.title}', view=QueueButton(state))
                except Exception:
                    # fallback: send unique text only
                    try:
                        await send_unique(ctx.channel, content=f'Enqueued: {item.title}')
                    except Exception:
                        pass
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Play(bot))
