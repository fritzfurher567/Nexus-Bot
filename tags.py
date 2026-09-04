"""
tags.py
Reusable text snippets ("tags") members can recall by name — handy for
FAQs, rules, or copy-paste answers staff give a lot.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tag-create", description="Create or update a tag")
    async def tag_create(self, interaction: discord.Interaction, name: str, content: str):
        await db.add_tag(interaction.guild_id, name, content, interaction.user.id, datetime.datetime.utcnow().isoformat())
        await interaction.response.send_message(f"Tag `{name}` saved.", ephemeral=True)

    @app_commands.command(name="tag", description="Show a saved tag")
    async def tag(self, interaction: discord.Interaction, name: str):
        row = await db.get_tag(interaction.guild_id, name)
        if not row:
            await interaction.response.send_message(f"No tag called `{name}`.", ephemeral=True)
            return
        await interaction.response.send_message(row["content"])

    @app_commands.command(name="tag-delete", description="[Mod] Delete a tag")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def tag_delete(self, interaction: discord.Interaction, name: str):
        deleted = await db.delete_tag(interaction.guild_id, name)
        if deleted:
            await interaction.response.send_message(f"Deleted tag `{name}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No tag called `{name}`.", ephemeral=True)

    @app_commands.command(name="tag-list", description="List all tags in this server")
    async def tag_list(self, interaction: discord.Interaction):
        names = await db.get_all_tags(interaction.guild_id)
        if not names:
            await interaction.response.send_message("No tags yet.", ephemeral=True)
            return
        await interaction.response.send_message(", ".join(f"`{n}`" for n in names))


async def setup(bot):
    await bot.add_cog(Tags(bot))
