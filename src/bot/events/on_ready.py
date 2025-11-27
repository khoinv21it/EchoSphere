import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
GUILD_ID = os.getenv('GUILD_ID')

async def on_ready(bot: commands.Bot):
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        if GUILD_ID:
            try:
                guild = discord.Object(id=int(GUILD_ID))
                await bot.tree.sync(guild=guild)
                print('Synced commands for guild', GUILD_ID)
            except Exception as e:
                print('Failed to sync guild commands', e)
                await bot.tree.sync()
        else:
            await bot.tree.sync()
            print('Synced global commands')
    except Exception as e:
        print('Command sync failed', e)
