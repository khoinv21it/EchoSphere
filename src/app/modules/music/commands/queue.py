import discord
from discord.ext import commands
from app.services.player import Queue

class QueueCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='queue', aliases=['q'])
    async def queue_cmd(self, ctx: commands.Context):
        # quick queue dump
        state = None
        from app.services.session import guild_states
        state = guild_states.get(ctx.guild.id)
        if not state or state.queue.length==0:
            return await ctx.reply('Queue is empty')
        lines = [f"{i+1}. {t.title} — {t.requested_by or 'Unknown'}" for i,t in enumerate(state.queue.list)]
        await ctx.reply('\n'.join(lines[:30]))


async def setup(bot: commands.Bot):
    await bot.add_cog(QueueCommand(bot))
