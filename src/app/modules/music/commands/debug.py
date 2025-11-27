import discord
from discord.ext import commands

class DebugCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='cmds')
    async def list_commands(self, ctx: commands.Context):
        cmds = sorted(set(c.name for c in self.bot.commands))
        cogs = sorted(list(self.bot.cogs.keys()))
        await ctx.reply(f"Commands ({len(cmds)}): {', '.join(cmds)}\nCogs ({len(cogs)}): {', '.join(cogs)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(DebugCommands(bot))
