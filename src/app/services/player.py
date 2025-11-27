import asyncio
from dataclasses import dataclass
from typing import Optional, List
import discord
from app.utils.ytdl import YTDL
import os
import contextlib

YTDL_OPTS = {'format': 'bestaudio/best', 'quiet': True, 'skip_download': True}
# YTDL is created in app.utils.ytdl

@dataclass
class Track:
    title: str
    url: str
    duration: int = 0
    requested_by: Optional[str] = None
    thumbnail: Optional[str] = None
    source_id: Optional[str] = None

class Queue:
    def __init__(self):
        self.tracks: List[Track] = []
        self.loop = False
        self.autoplay = False

    def enqueue(self, t: Track):
        self.tracks.append(t)

    def dequeue(self) -> Optional[Track]:
        if not self.tracks: return None
        return self.tracks.pop(0)

    def pop_last(self) -> Optional[Track]:
        if not self.tracks: return None
        return self.tracks.pop()

    def remove_at(self, idx: int) -> Optional[Track]:
        if idx < 0 or idx >= len(self.tracks): return None
        return self.tracks.pop(idx)

    def clear(self):
        self.tracks.clear()

    def shuffle(self):
        import random
        random.shuffle(self.tracks)

    @property
    def length(self):
        return len(self.tracks)

    @property
    def list(self):
        return self.tracks.copy()


# Helper to call YTDL.extract_info while redirecting stdout/stderr to devnull
def _extract_info_silent(arg, download=False):
    try:
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stderr(devnull), contextlib.redirect_stdout(devnull):
                return YTDL.extract_info(arg, download=download)
    except Exception:
        # fallback to normal call (let exceptions propagate to caller)
        return YTDL.extract_info(arg, download=download)


async def ytdl_search(query: str, max_results: int = 5) -> List[Track]:
    loop = asyncio.get_event_loop()
    q = f"ytsearch{max_results}:{query}"
    info = await loop.run_in_executor(None, _extract_info_silent, q, False)
    entries = info.get('entries', []) if isinstance(info, dict) else []
    return [Track(title=e.get('title'), url=e.get('webpage_url'), duration=int(e.get('duration') or 0), thumbnail=e.get('thumbnail'), source_id=e.get('id')) for e in entries]


async def ytdl_info(url: str) -> Optional[dict]:
    loop = asyncio.get_event_loop()
    try:
        info = await loop.run_in_executor(None, _extract_info_silent, url, False)
        return info
    except Exception:
        return None


async def play_next(bot: discord.Client, state, guild_id: int, ffmpeg_options: Optional[dict] = None):
    # State must have queue, voice_client, current_track
    if not state or not state.voice_client:
        return
    if not ffmpeg_options:
        ffmpeg_options = {'options': '-vn -nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

    prev = state.current_track

    # autoplay logic if empty
    if state.queue.length == 0 and not state.current_track:
        if state.queue.autoplay and prev:
            results = await ytdl_search(prev.title, max_results=5)
            if results:
                state.queue.enqueue(results[0])
        else:
            return

    nxt = state.queue.dequeue()
    if not nxt:
        state.current_track = None
        return

    state.current_track = nxt

    # push previous into history
    try:
        if getattr(state, 'history', None) is not None and prev is not None:
            state.history.insert(0, prev)
    except Exception:
        pass

    info = await ytdl_info(nxt.url)
    if not info:
        # fallback: try to message last_text_channel
        if hasattr(state, 'last_text_channel') and state.last_text_channel:
            try:
                await state.last_text_channel.send(f'Failed to get info for {nxt.title}, skipping')
            except Exception:
                pass
        else:
            print(f'Failed to get info for {nxt.title}, skipping')
        state.current_track = None
        return await play_next(bot, state, guild_id, ffmpeg_options)

    url_to_play = info.get('url')
    if not url_to_play:
        formats = info.get('formats', [])
        for f in reversed(formats):
            if f.get('acodec') != 'none':
                url_to_play = f.get('url')
                break
    if not url_to_play:
        if hasattr(state, 'last_text_channel') and state.last_text_channel:
            try:
                await state.last_text_channel.send(f'No playable stream for {nxt.title}, skipping')
            except Exception:
                pass
        else:
            print(f'No playable stream for {nxt.title}, skipping')
        state.current_track = None
        return await play_next(bot, state, guild_id, ffmpeg_options)

    # Allow overriding ffmpeg executable via env var FFMPEG_EXECUTABLE or FFMPEG_PATH
    ffmpeg_executable = os.getenv('FFMPEG_EXECUTABLE') or os.getenv('FFMPEG_PATH')

    try:
        # Ensure voice client is connected before attempting to play (avoid "Not connected to voice.")
        # Wait briefly for handshake if needed
        for _ in range(20):
            try:
                if getattr(state.voice_client, 'is_connected', lambda: False)():
                    break
            except Exception:
                pass
            await asyncio.sleep(0.1)

        if not getattr(state.voice_client, 'is_connected', lambda: False)():
            print('play error: voice client not connected after wait')
            # try to inform channel
            if hasattr(state, 'last_text_channel') and state.last_text_channel:
                try:
                    await state.last_text_channel.send('Audio playback failed: voice client not connected yet. Please try again in a moment.')
                except Exception:
                    pass
            state.current_track = None
            return

        if ffmpeg_executable:
            source = discord.FFmpegPCMAudio(url_to_play, executable=ffmpeg_executable, **ffmpeg_options)
        else:
            source = discord.FFmpegPCMAudio(url_to_play, **ffmpeg_options)

        if state.voice_client.is_playing():
            state.voice_client.stop()
        # make 'after' callback call on_track_end with state
        state.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(on_track_end(bot, state, e), bot.loop))

        # update now playing message (import at runtime to avoid circular imports)
        try:
            from app.services.session import update_now_playing_message
            await update_now_playing_message(bot, state)
        except Exception as e:
            print('failed to update now playing message', e)

        # Update now playing should be scheduled elsewhere
    except discord.errors.ClientException as e:
        # Common cause: ffmpeg not found; inform channel and log
        msg = str(e)
        print('play error', e)
        if 'ffmpeg' in msg.lower() or 'executable' in msg.lower():
            if hasattr(state, 'last_text_channel') and state.last_text_channel:
                try:
                    await state.last_text_channel.send("Audio playback failed: ffmpeg was not found.\nInstall ffmpeg and add it to PATH, or set the FFMPEG_EXECUTABLE environment variable to the ffmpeg executable path.")
                except Exception:
                    pass
            else:
                print('ffmpeg was not found; set FFMPEG_EXECUTABLE or add ffmpeg to PATH')
            state.current_track = None
            return
        # handle not connected error by notifying and returning
        if 'not connected' in msg.lower():
            if hasattr(state, 'last_text_channel') and state.last_text_channel:
                try:
                    await state.last_text_channel.send('Audio playback failed: voice client not connected.')
                except Exception:
                    pass
            state.current_track = None
            return
        state.current_track = None
        return await play_next(bot, state, guild_id, ffmpeg_options)
    except Exception as e:
        print('play error', e)
        state.current_track = None
        return await play_next(bot, state, guild_id, ffmpeg_options)


async def on_track_end(bot: discord.Client, state, error):
    # simple handler: restart play
    if not state: return
    prev = state.current_track
    state.current_track = None
    if state.queue.loop and prev:
        state.queue.enqueue(prev)
    if state.queue.length == 0 and state.queue.autoplay and prev:
        results = await ytdl_search(prev.title, max_results=5)
        if results:
            state.queue.enqueue(results[0])
    await asyncio.sleep(0.5)
    await play_next(bot, state, None)