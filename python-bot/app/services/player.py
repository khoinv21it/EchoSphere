import asyncio
from dataclasses import dataclass
from typing import Optional, List
import os
import contextlib

# Use the shared YTDL instance configured in app.utils.ytdl to ensure
# extractor_args and a silent logger are applied (avoids EJS warnings).
from app.utils.ytdl import YTDL


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


# Helper to call YTDL.extract_info while redirecting stdout/stderr to devnull
def _extract_info_silent(arg, download=False):
    try:
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stderr(devnull), contextlib.redirect_stdout(devnull):
                return YTDL.extract_info(arg, download=download)
    except Exception:
        return YTDL.extract_info(arg, download=download)


async def ytdl_search(query: str, max_results: int = 5):
    q = f"ytsearch{max_results}:{query}"
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _extract_info_silent, q, False)
    entries = info.get('entries', []) if isinstance(info, dict) else []
    return [Track(title=e.get('title'), url=e.get('webpage_url'), duration=int(e.get('duration') or 0), thumbnail=e.get('thumbnail')) for e in entries]
