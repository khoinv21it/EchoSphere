import os
import asyncio
from dotenv import load_dotenv

import discord

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
GUILD_ID = os.getenv('GUILD_ID')

async def on_ready(bot: discord.Client):
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    # register commands
    try:
        if GUILD_ID:
            try:
                guild = discord.Object(id=int(GUILD_ID))
                await bot.tree.sync(guild=guild)
                print('Synced commands for guild', GUILD_ID)
            except Exception as e:
                print('Failed to sync guild commands', e)
                await bot.tree.sync()  # fallback to global
        else:
            await bot.tree.sync()
            print('Synced global commands')
    except Exception as e:
        print('Command sync failed', e)



