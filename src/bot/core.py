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
        # allow command prefix override
        prefix = kwargs.pop('command_prefix', '!')
        super().__init__(command_prefix=prefix, intents=intents, case_insensitive=True)

    async def setup_hook(self):
        # import events and register; create wrappers so the event functions receive the bot instance
        from .events.on_ready import on_ready
        from .events.on_message import on_message

        async def _on_ready_wrapper():
            try:
                await on_ready(self)
            except Exception as e:
                print('on_ready handler failed', e)

        async def _on_message_wrapper(message):
            try:
                await on_message(self, message)
            except Exception as e:
                print('on_message handler failed', e)

        self.add_listener(_on_ready_wrapper, 'on_ready')
        self.add_listener(_on_message_wrapper, 'on_message')

        # auto-load music module cogs
        try:
            from app.modules.music.commands import __main__ as music_commands
            await music_commands.setup(self)
            print('Loaded music commands')
            # diagnostic: list registered commands
            cmds = [c.name for c in self.commands]
            print('Registered prefix commands:', cmds)
            cogs = list(self.cogs.keys())
            print('Loaded cogs:', cogs)
        except Exception as e:
            print('Failed to load music commands', e)
        return


def build_bot(command_prefix='!', **kwargs):
    intents = kwargs.pop('intents', None)
    return BotCore(command_prefix=command_prefix, intents=intents)
