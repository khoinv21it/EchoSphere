import discord
from discord.ext import commands

async def on_message(bot: commands.Bot, message: discord.Message):
    if message.author.bot: return
    if not message.guild: return
    # handle prefix commands and other message-based logic
    await bot.process_commands(message)
