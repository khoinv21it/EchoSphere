import discord

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
