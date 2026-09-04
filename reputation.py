"""
reputation.py
Give members reputation points (once per day per giver) to recognize
helpfulness.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Reputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rep-give", description="Give another member a reputation point (once per day)")
    async def rep_give(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You can't rep yourself.", ephemeral=True)
            return
        today = datetime.date.today().isoformat()
        already_given = await db.has_given_rep_today(interaction.guild_id, interaction.user.id, today)
        if already_given:
            await interaction.response.send_message("You've already given rep today. Try again tomorrow.", ephemeral=True)
            return
        await db.add_reputation(interaction.guild_id, member.id, interaction.user.id, datetime.datetime.utcnow().isoformat())
        await interaction.response.send_message(f"⭐ {interaction.user.mention} gave a reputation point to {member.mention}!")

    @app_commands.command(name="rep-check", description="Check a member's reputation")
    async def rep_check(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        count = await db.get_reputation_count(interaction.guild_id, member.id)
        await interaction.response.send_message(f"⭐ {member.display_name} has **{count}** reputation point(s).")

    @app_commands.command(name="rep-leaderboard", description="Top reputation in this server")
    async def rep_leaderboard(self, interaction: discord.Interaction):
        rows = await db.get_reputation_leaderboard(interaction.guild_id)
        lines = []
        for i, r in enumerate(rows, 1):
            member = interaction.guild.get_member(r["user_id"])
            name = member.display_name if member else f"User {r['user_id']}"
            lines.append(f"**{i}.** {name} — {r['total']} rep")
        embed = discord.Embed(title="⭐ Reputation Leaderboard", description="\n".join(lines) or "No data yet.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Reputation(bot))
