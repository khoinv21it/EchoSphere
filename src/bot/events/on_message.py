import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

async def on_message(bot: commands.Bot, message: discord.Message):
    if message.author.bot: return
    if not message.guild: return
    await bot.process_commands(message)
