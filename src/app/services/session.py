from typing import Dict
from dataclasses import dataclass
import discord
from app.services.player import Queue


class NowPlayingControls(discord.ui.View):
    def __init__(self, bot, state):
        super().__init__(timeout=None)
        self.bot = bot
        self.state = state

    @discord.ui.button(label='⏯️', style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.state
        if not state or not state.voice_client:
            return await interaction.response.send_message('Not connected', ephemeral=True)
        if state.voice_client.is_playing():
            state.voice_client.pause()
            await interaction.response.send_message('Paused', ephemeral=True)
        else:
            state.voice_client.resume()
            await interaction.response.send_message('Resumed', ephemeral=True)

    @discord.ui.button(label='⏭️', style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.state
        if not state or not state.voice_client:
            return await interaction.response.send_message('Not connected', ephemeral=True)
        try:
            # stop current track; player.on_track_end/play_next will handle next
            state.voice_client.stop()
            # call play_next to advance immediately
            try:
                from app.services.player import play_next
                await play_next(self.bot, state, interaction.guild.id)
            except Exception as e:
                print('skip -> play_next failed', e)
            await interaction.response.send_message('Skipped', ephemeral=True)
        except Exception:
            await interaction.response.send_message('Failed to skip', ephemeral=True)

    @discord.ui.button(label='⏹️', style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.state
        if not state or not state.voice_client:
            return await interaction.response.send_message('Not connected', ephemeral=True)
        try:
            state.voice_client.stop()
            state.queue.clear()
            state.current_track = None
            await interaction.response.send_message('Stopped and cleared queue', ephemeral=True)
        except Exception:
            await interaction.response.send_message('Failed to stop', ephemeral=True)


@dataclass
class GuildState:
    queue: Queue
    voice_client: discord.VoiceClient = None
    current_track = None
    now_playing_message = None
    pagination_message = None
    pagination_page = 0
    pending_searches = None
    last_text_channel = None
    history = None


# global map
guild_states: Dict[int, GuildState] = {}

async def ensure_guild_state(guild: discord.Guild, create=True):
    st = guild_states.get(guild.id)
    if not st and create:
        st = GuildState(queue=Queue())
        st.pending_searches = {}
        st.last_text_channel = None
        st.history = []
        guild_states[guild.id] = st
    return st


async def send_text_channel(state: GuildState, content: str):
    if state and state.last_text_channel:
        try:
            await state.last_text_channel.send(content)
            return True
        except Exception:
            return False
    print('MESSAGE:', content)
    return False


async def connect_voice(state: GuildState, channel: discord.VoiceChannel):
    """Connect or move the bot's voice client for the guild and update state.voice_client.

    Handles cases where a VoiceClient already exists on the guild (possibly created
    by other code paths) to avoid ClientException: Already connected to a voice channel.
    """
    if not channel:
        return
    try:
        # If state already has a voice_client and it's connected
        if state.voice_client and getattr(state.voice_client, 'is_connected', lambda: False)():
            if state.voice_client.channel.id == channel.id:
                return state.voice_client
            try:
                await state.voice_client.move_to(channel)
                return state.voice_client
            except Exception:
                # fallthrough to reconnect
                pass

        # Check guild-level voice client (discord.Guild.voice_client) — safer than assuming state
        guild_vc = getattr(channel.guild, 'voice_client', None)
        if guild_vc and getattr(guild_vc, 'is_connected', lambda: False)():
            # If already connected to the target channel, reuse it
            if guild_vc.channel.id == channel.id:
                state.voice_client = guild_vc
                return guild_vc
            # otherwise move it
            try:
                await guild_vc.move_to(channel)
                state.voice_client = guild_vc
                return guild_vc
            except Exception:
                pass

        # No existing voice client, create a new one
        vc = await channel.connect()
        state.voice_client = vc
        return vc
    except discord.errors.ClientException as e:
        # Likely "Already connected to a voice channel." — try to recover by using guild.voice_client
        try:
            guild_vc = getattr(channel.guild, 'voice_client', None)
            if guild_vc:
                state.voice_client = guild_vc
                # if it's not in the desired channel, try moving
                if guild_vc.channel.id != channel.id:
                    try:
                        await guild_vc.move_to(channel)
                    except Exception:
                        pass
                return state.voice_client
        except Exception:
            pass
        # re-raise if we couldn't recover
        raise
    except Exception as e:
        print('Failed to connect to voice channel', e)
        raise


async def update_now_playing_message(bot, state: GuildState):
    try:
        track = state.current_track
        if not track:
            # if no track, clear existing message
            if state.now_playing_message:
                try:
                    await state.now_playing_message.delete()
                except Exception:
                    pass
                state.now_playing_message = None
            return

        # Always send a fresh now-playing message for each track change so users
        # clearly see the new controls and embed (avoid confusing edits/duplicates).
        # Delete the previous message if present.
        if state.now_playing_message:
            try:
                await state.now_playing_message.delete()
            except Exception:
                pass
            state.now_playing_message = None

        if not state.last_text_channel:
            return

        embed = discord.Embed(title='Now Playing', description=f'**{track.title}**', color=0x1DB954)
        embed.add_field(name='Requested By', value=track.requested_by or 'Unknown', inline=True)
        embed.add_field(name='Duration', value=f'{track.duration}s', inline=True)
        if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
        try:
            # attach interactive controls
            view = NowPlayingControls(bot, state)
            state.now_playing_message = await state.last_text_channel.send(embed=embed, view=view)
        except Exception as e:
            print('Failed to send now playing message', e)
            # fallback: use send_unique to avoid duplicate messages
            try:
                from app.utils.discord.helpers import send_unique
                state.now_playing_message = await send_unique(state.last_text_channel, embed=embed)
            except Exception:
                pass
    except Exception as ex:
        print('update now playing failed', ex)
