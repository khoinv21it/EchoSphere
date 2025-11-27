import yt_dlp

# Provide extractor args to avoid EJS warnings on YouTube when no JS runtime is available.
# If you want full JS extraction support, install a JS runtime on the system (node, quickjs, etc.).
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'skip_download': True,
    'extractor_args': {
        'youtube': {
            'player_client': 'default'
        }
    }
}

YTDL = yt_dlp.YoutubeDL(YTDL_OPTS)
