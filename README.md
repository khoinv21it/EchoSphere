Python Discord Music Bot

This is a minimal but featureful Discord music bot built with Python that supports both slash commands and prefix commands, YouTube search with selection, playlist support, autoplay, and a paginated queue embed.

Features:

- Slash and Prefix (! by default) command support for music features: play, skip, stop, pause, resume, queue, nowplaying, shuffle, loop, remove, autoplay, playlist, join, select
- Interactive search using top 5 results and text selection or button selection
- Playlist support using youtube_dl/yt-dlp
- Autoplay toggle to play a similar track when queue ends
- Queue model with metadata (title, url, duration, thumbnail, source, requested_by)

Usage:

1. Copy .env.example to .env and set DISCORD_TOKEN and CLIENT_ID.
2. Install dependencies: pip install -r requirements.txt
3. Run the bot: python bot.py

Notes:

- This is intended as a starting point; tweak and extend as needed!
