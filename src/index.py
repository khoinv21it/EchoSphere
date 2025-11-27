from dotenv import load_dotenv
import os
import sys
import pathlib

# Disable writing .pyc files at runtime to avoid creating __pycache__ folders
sys.dont_write_bytecode = True

# Ensure src is on sys.path so importing 'app' package works when running from project root
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.core import build_bot

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX', '!')

bot = build_bot(command_prefix=PREFIX)

if __name__ == '__main__':
    if not TOKEN:
        print('DISCORD_TOKEN is not set in environment')
    else:
        bot.run(TOKEN)
