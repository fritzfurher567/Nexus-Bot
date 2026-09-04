"""
autoresponder.py
Simple trigger-word -> auto-reply system, distinct from Custom Commands.py
(which is presumably prefix/slash-command based) — this fires on any
message containing the trigger word.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Autoresponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="autoresponder-add", description="[Mod] Add a trigger word -> auto-reply")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autoresponder_add(self, interaction: discord.Interaction, trigger: str, response: str):
        await db.add_autoresponder(interaction.guild_id, trigger, response)
        await interaction.response.send_message(f"Added autoresponder for `{trigger}`.", ephemeral=True)

    @app_commands.command(name="autoresponder-remove", description="[Mod] Remove an autoresponder")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autoresponder_remove(self, interaction: discord.Interaction, trigger: str):
        removed = await db.remove_autoresponder(interaction.guild_id, trigger)
        if removed:
            await interaction.response.send_message(f"Removed autoresponder for `{trigger}`.", ephemeral=True)
        else:
            await interaction.response.send_message("No autoresponder with that trigger.", ephemeral=True)

    @app_commands.command(name="autoresponder-list", description="List all autoresponders")
    async def autoresponder_list(self, interaction: discord.Interaction):
        rows = await db.get_autoresponders(interaction.guild_id)
        if not rows:
            await interaction.response.send_message("No autoresponders set up.", ephemeral=True)
            return
        await interaction.response.send_message(", ".join(f"`{r['trigger']}`" for r in rows), ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        rows = await db.get_autoresponders(message.guild.id)
        if not rows:
            return
        content_lower = message.content.lower()
        for r in rows:
            if r["trigger"] in content_lower:
                await message.channel.send(r["response"])
                break  # only fire the first match to avoid spam


async def setup(bot):
    await bot.add_cog(Autoresponder(bot))
