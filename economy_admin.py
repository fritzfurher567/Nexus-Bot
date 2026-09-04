"""
economy_admin.py
Admin-only economy management + a personal networth summary.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database as db

CURRENCY = "£"


class EconomyAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="economy-set", description="[Admin] Set a member's wallet balance directly")
    @app_commands.checks.has_permissions(administrator=True)
    async def economy_set(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await db.get_balance_data(interaction.guild_id, member.id)  # ensure row exists
        await db.update_balance(interaction.guild_id, member.id, amount)
        await interaction.response.send_message(f"Set {member.mention}'s balance to **{CURRENCY}{amount:,}**.", ephemeral=True)

    @app_commands.command(name="economy-reset", description="[Admin] Reset a member's balance and bank to zero")
    @app_commands.checks.has_permissions(administrator=True)
    async def economy_reset(self, interaction: discord.Interaction, member: discord.Member):
        await db.get_balance_data(interaction.guild_id, member.id)
        await db.update_balance(interaction.guild_id, member.id, 0)
        await db.set_bank(interaction.guild_id, member.id, 0)
        await interaction.response.send_message(f"Reset {member.mention}'s economy data.", ephemeral=True)

    @app_commands.command(name="networth", description="See your (or someone's) total net worth (wallet + bank)")
    async def networth(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        row = await db.get_balance_data(interaction.guild_id, member.id)
        total = row["balance"] + (row.get("bank", 0) or 0)
        await interaction.response.send_message(f"{member.display_name}'s net worth: **{CURRENCY}{total:,}**")


async def setup(bot):
    await bot.add_cog(EconomyAdmin(bot))
