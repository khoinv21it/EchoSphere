import discord
from discord.ext import commands
from discord import app_commands

class SkipCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(ctx.guild)
        if not state or not state.voice_client:
            return await ctx.reply('Nothing to skip')
        state.voice_client.stop()
        await ctx.reply('Skipped')

    @app_commands.command(name='skip', description='Skip the current track')
    async def slash_skip(self, interaction: discord.Interaction):
        from app.services.session import ensure_guild_state
        state = await ensure_guild_state(interaction.guild)
        if not state or not state.voice_client:
            return await interaction.response.send_message('Nothing to skip', ephemeral=True)
        state.voice_client.stop()
        await interaction.response.send_message('Skipped', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SkipCommand(bot))
