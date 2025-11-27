from typing import Dict
from dataclasses import dataclass
import discord
from app.services.player import Queue

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


# global map
guild_states: Dict[int, GuildState] = {}

async def ensure_guild_state(guild: discord.Guild, create=True):
    st = guild_states.get(guild.id)
    if not st and create:
        st = GuildState(queue=Queue())
        st.pending_searches = {}
        st.last_text_channel = None
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


async def update_now_playing_message(state: GuildState):
    try:
        if not state.now_playing_message:
            if not state.last_text_channel: return
            track = state.current_track
            if not track: return
            embed = discord.Embed(title='Now Playing', description=f'**{track.title}**', color=0x1DB954)
            embed.add_field(name='Requested By', value=track.requested_by or 'Unknown', inline=True)
            embed.add_field(name='Duration', value=f'{track.duration}s', inline=True)
            if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
            try:
                state.now_playing_message = await state.last_text_channel.send(embed=embed)
            except Exception as e:
                print('Failed to send now playing message', e)
            return
        # update existing message
        track = state.current_track
        if not track:
            try:
                await state.now_playing_message.edit(content='No track', embed=None)
            except Exception:
                pass
            return
        embed = discord.Embed(title='Now Playing', description=f'**{track.title}**', color=0x1DB954)
        embed.add_field(name='Requested By', value=track.requested_by or 'Unknown', inline=True)
        embed.add_field(name='Duration', value=f'{track.duration}s', inline=True)
        if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
        try:
            await state.now_playing_message.edit(embed=embed)
        except Exception:
            pass
    except Exception as ex:
        print('update now playing failed', ex)
