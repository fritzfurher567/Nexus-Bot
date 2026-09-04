"""
suggestions.py
Suggestion box: members submit via /suggest, it posts to a review channel
with up/down vote reactions, staff can approve/deny.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggestions-channel", description="[Admin] Set the channel suggestions get posted to")
    @app_commands.checks.has_permissions(administrator=True)
    async def suggestions_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.set_suggestions_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Suggestions will now post in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="suggest", description="Submit a suggestion")
    async def suggest(self, interaction: discord.Interaction, content: str):
        config = await db.get_suggestions_config(interaction.guild_id)
        if not config["channel_id"]:
            await interaction.response.send_message("Suggestions aren't set up yet. Ask an admin to run /suggestions-channel.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(config["channel_id"])
        if not channel:
            await interaction.response.send_message("Configured suggestions channel no longer exists.", ephemeral=True)
            return

        timestamp = datetime.datetime.utcnow().isoformat()
        suggestion_id = await db.add_suggestion(interaction.guild_id, interaction.user.id, config["channel_id"], content, timestamp)

        embed = discord.Embed(
            title=f"Suggestion #{suggestion_id}",
            description=content,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Submitted by {interaction.user}")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await db.set_suggestion_message(suggestion_id, msg.id)

        await interaction.response.send_message(f"Suggestion #{suggestion_id} submitted!", ephemeral=True)

    @app_commands.command(name="suggestion-status", description="[Admin] Mark a suggestion approved/denied/pending")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(status=[
        app_commands.Choice(name="Approved", value="approved"),
        app_commands.Choice(name="Denied", value="denied"),
        app_commands.Choice(name="Pending", value="pending"),
    ])
    async def suggestion_status(self, interaction: discord.Interaction, suggestion_id: int, status: app_commands.Choice[str]):
        suggestion = await db.get_suggestion(suggestion_id)
        if not suggestion or suggestion["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("Suggestion not found.", ephemeral=True)
            return

        await db.set_suggestion_status(suggestion_id, status.value)

        color = {"approved": discord.Color.green(), "denied": discord.Color.red(), "pending": discord.Color.greyple()}[status.value]
        channel = interaction.guild.get_channel(suggestion["channel_id"])
        if channel and suggestion["message_id"]:
            try:
                msg = await channel.fetch_message(suggestion["message_id"])
                embed = msg.embeds[0]
                embed.color = color
                embed.title = f"Suggestion #{suggestion_id} — {status.name}"
                await msg.edit(embed=embed)
            except discord.NotFound:
                pass

        await interaction.response.send_message(f"Suggestion #{suggestion_id} marked **{status.name}**.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
