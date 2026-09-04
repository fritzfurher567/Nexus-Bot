"""
confessions.py
Anonymous numbered confessions posted to a designated channel.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Confessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="confessions-channel", description="[Admin] Set the anonymous confessions channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def confessions_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.set_confessions_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Confessions will post anonymously in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="confess", description="Post an anonymous confession")
    async def confess(self, interaction: discord.Interaction, content: str):
        config = await db.get_confessions_config(interaction.guild_id)
        if not config["channel_id"]:
            await interaction.response.send_message("Confessions aren't set up here yet.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(config["channel_id"])
        if not channel:
            await interaction.response.send_message("Configured confessions channel no longer exists.", ephemeral=True)
            return

        number = await db.next_confession_number(interaction.guild_id)
        embed = discord.Embed(title=f"Anonymous Confession #{number}", description=content, color=discord.Color.dark_grey())
        await channel.send(embed=embed)
        await interaction.response.send_message("Your confession was posted anonymously.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Confessions(bot))
