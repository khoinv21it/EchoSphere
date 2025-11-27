import discord
from discord.ext import commands

class SelectCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='select')
    async def select(self, ctx: commands.Context, index: int):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        pending = state.pending_searches.get(ctx.author.id) if state.pending_searches else None
        if not pending:
            return await ctx.reply('No pending search for you')
        if index < 1 or index > len(pending):
            return await ctx.reply('Invalid selection')
        item = pending[index-1]
        state.queue.enqueue(item)
        del state.pending_searches[ctx.author.id]
        if not state.voice_client or not state.voice_client.is_connected():
            if ctx.author.voice and ctx.author.voice.channel:
                from app.services.session import connect_voice
                await connect_voice(state, ctx.author.voice.channel)
        if not state.current_track:
            from app.services.player import play_next
            await play_next(self.bot, state, ctx.guild.id)
        await ctx.reply(f'Enqueued: {item.title}')


async def setup(bot: commands.Bot):
    await bot.add_cog(SelectCommand(bot))
