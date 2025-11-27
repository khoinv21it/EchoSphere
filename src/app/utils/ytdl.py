import yt_dlp

# Provide extractor args to avoid EJS warnings on YouTube when no JS runtime is available.
# If you want full JS extraction support, install a JS runtime on the system (node, quickjs, etc.).
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'extractor_args': {
        'youtube': {
            'player_client': 'default'
        }
    }
}

class _SilentLogger:
    def debug(self, msg):
        return
    def warning(self, msg):
        # swallow yt-dlp warnings
        return
    def error(self, msg):
        # still print errors to console
        print(msg)

# Use a silent logger so yt-dlp warnings don't spam the bot logs.
YTDL = yt_dlp.YoutubeDL({**YTDL_OPTS, 'logger': _SilentLogger()})
