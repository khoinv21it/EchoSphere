import asyncio
import yt_dlp
from dataclasses import dataclass
from typing import Optional, List

YTDL_OPTS = {'format': 'bestaudio/best', 'quiet': True, 'skip_download': True}
YTDL = yt_dlp.YoutubeDL(YTDL_OPTS)

@dataclass
class Track:
    title: str
    url: str
    duration: int = 0
    requested_by: Optional[str] = None
    thumbnail: Optional[str] = None

class Queue:
    def __init__(self):
        self.tracks: List[Track] = []
        self.loop = False
        self.autoplay = False

    def enqueue(self, t: Track):
        self.tracks.append(t)

    def dequeue(self):
        return self.tracks.pop(0) if self.tracks else None

    def remove_at(self, idx):
        if idx<0 or idx>=len(self.tracks): return None
        return self.tracks.pop(idx)

    def clear(self):
        self.tracks.clear()

    def shuffle(self):
        import random
        random.shuffle(self.tracks)


async def ytdl_search(query: str, max_results: int = 5):
    q = f"ytsearch{max_results}:{query}"
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, lambda: YTDL.extract_info(q, download=False))
    entries = info.get('entries', []) if isinstance(info, dict) else []
    return [Track(title=e.get('title'), url=e.get('webpage_url'), duration=int(e.get('duration') or 0), thumbnail=e.get('thumbnail')) for e in entries]
