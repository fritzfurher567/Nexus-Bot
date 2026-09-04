"""
quotes.py
Save memorable server quotes and pull them up later.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="quote-add", description="Save a quote")
    async def quote_add(self, interaction: discord.Interaction, content: str, said_by: discord.Member = None):
        quote_id = await db.add_quote(
            interaction.guild_id,
            said_by.id if said_by else None,
            content,
            interaction.user.id,
            datetime.datetime.utcnow().isoformat(),
        )
        await interaction.response.send_message(f"Saved as quote #{quote_id}.", ephemeral=True)

    @app_commands.command(name="quote", description="Get a random saved quote")
    async def quote(self, interaction: discord.Interaction):
        q = await db.get_random_quote(interaction.guild_id)
        if not q:
            await interaction.response.send_message("No quotes saved yet.", ephemeral=True)
            return
        author = interaction.guild.get_member(q["author_id"]) if q["author_id"] else None
        embed = discord.Embed(description=f'"{q["content"]}"', color=discord.Color.blurple())
        embed.set_footer(text=f"— {author.display_name if author else 'Unknown'} · #{q['id']}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quotes-list", description="List all saved quotes")
    async def quotes_list(self, interaction: discord.Interaction):
        quotes = await db.get_all_quotes(interaction.guild_id)
        if not quotes:
            await interaction.response.send_message("No quotes saved yet.", ephemeral=True)
            return
        lines = [f"**#{q['id']}** — {q['content'][:80]}" for q in quotes[:15]]
        embed = discord.Embed(title="📜 Quotes", description="\n".join(lines), color=discord.Color.blurple())
        if len(quotes) > 15:
            embed.set_footer(text=f"Showing 15 of {len(quotes)} quotes")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quote-delete", description="[Admin] Delete a quote by ID")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def quote_delete(self, interaction: discord.Interaction, quote_id: int):
        deleted = await db.delete_quote(interaction.guild_id, quote_id)
        if deleted:
            await interaction.response.send_message(f"Deleted quote #{quote_id}.", ephemeral=True)
        else:
            await interaction.response.send_message("Quote not found.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Quotes(bot))
