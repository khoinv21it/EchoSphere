import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

class BotCore(commands.Bot):
    def __init__(self, **kwargs):
        intents = kwargs.pop('intents', None)
        if not intents:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.voice_states = True
            intents.messages = True
        super().__init__(command_prefix=kwargs.pop('command_prefix', '!'), intents=intents)
        # placeholder

    async def setup_hook(self):
        # load cogs or register here
        return


def build_bot(command_prefix='!', **kwargs):
    intents = kwargs.pop('intents', None)
    return BotCore(command_prefix=command_prefix, intents=intents)
