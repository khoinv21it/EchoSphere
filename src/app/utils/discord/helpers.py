import discord
import time
from typing import Optional

# short-term cache of recently sent messages to avoid repeated identical messages
# key -> (message_id, timestamp)
_recent_sent = {}
_CACHE_TTL = 5.0  # seconds

def make_now_playing_embed(track, queue_len=0, options=None):
    if options is None: options = {}
    playing = options.get('playing', True)
    color = 0x1DB954
    embed = discord.Embed(title='Now Playing', description=f'**{track.title}**', color=color)
    embed.add_field(name='Requested By', value=track.requested_by or 'Unknown', inline=True)
    embed.add_field(name='Duration', value=f'{track.duration}s', inline=True)
    if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
    return embed


def make_queue_embed(queue, page=0, items_per_page=10, now_playing=None):
    total = queue.length
    total_pages = max(1, (total + items_per_page - 1) // items_per_page)
    start = page * items_per_page
    end = min(total, start + items_per_page)
    lines = []
    if now_playing:
        lines.append(f'Now Playing: **{now_playing.title}** — {now_playing.requested_by}')
    for i,t in enumerate(queue.list[start:end], start=start+1):
        lines.append(f'{i}. {t.title} — {t.requested_by or "Unknown"} ({t.duration}s)')
    embed = discord.Embed(title='Queue', description='\n'.join(lines))
    embed.set_footer(text=f'Page {page+1}/{total_pages} — {total} tracks')
    return embed


async def _fetch_cached_message(channel: discord.abc.Messageable, msg_id: int) -> Optional[discord.Message]:
    try:
        # channel may be TextChannel; try fetch_message if available
        if hasattr(channel, 'fetch_message'):
            return await channel.fetch_message(msg_id)
        # otherwise, fall back to scanning history
        async for m in channel.history(limit=20):
            if m.id == msg_id:
                return m
    except Exception:
        return None
    return None

async def send_unique(channel: discord.abc.Messageable, content: str = None, embed: discord.Embed = None):
    """Send a message to channel unless the bot has recently sent an identical message.
    Prevents accidental duplicate bot messages in quick succession.
    Uses a short in-memory cache to avoid scanning history every time.
    """
    try:
        key = None
        if content:
            key = f'text:{content}'
        elif embed:
            key = f'embed:{embed.title}|{embed.description}'
        now = time.time()
        if key:
            cached = _recent_sent.get((getattr(channel, 'id', None), key))
            if cached:
                msg_id, ts = cached
                if now - ts < _CACHE_TTL:
                    m = await _fetch_cached_message(channel, msg_id)
                    if m:
                        return m
                    else:
                        # stale cache entry
                        _recent_sent.pop((getattr(channel, 'id', None), key), None)

        # inspect recent messages in channel as fallback
        recent = []
        async for m in channel.history(limit=10):
            recent.append(m)
        for m in recent:
            if m.author.bot:
                if content and m.content == content:
                    # cache and return
                    try:
                        _recent_sent[(getattr(channel, 'id', None), key)] = (m.id, now)
                    except Exception:
                        pass
                    return m
                if embed and m.embeds:
                    try:
                        if m.embeds[0].title == embed.title and m.embeds[0].description == embed.description:
                            try:
                                _recent_sent[(getattr(channel, 'id', None), key)] = (m.id, now)
                            except Exception:
                                pass
                            return m
                    except Exception:
                        pass
        # not found, send
        sent = await channel.send(content=content, embed=embed)
        try:
            if key:
                _recent_sent[(getattr(channel, 'id', None), key)] = (sent.id, now)
        except Exception:
            pass
        return sent
    except Exception as e:
        print('send_unique failed', e)
        try:
            return await channel.send(content=content, embed=embed)
        except Exception:
            return None
