"""
temproles.py
Assign a role that automatically gets removed after a set duration —
useful for temp-muted-from-a-specific-channel roles, event roles, boosts,
trial periods, etc. Backed by a background task that checks for expiries.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database as db


def parse_duration(text: str) -> datetime.timedelta:
    unit = text[-1].lower()
    amount = int(text[:-1])
    return {
        "m": datetime.timedelta(minutes=amount),
        "h": datetime.timedelta(hours=amount),
        "d": datetime.timedelta(days=amount),
        "w": datetime.timedelta(weeks=amount),
    }[unit]


class TempRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_expiries.start()

    def cog_unload(self):
        self.check_expiries.cancel()

    @app_commands.command(name="temprole", description="[Mod] Give a member a role that expires automatically")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def temprole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role, duration: str):
        try:
            delta = parse_duration(duration)
        except (ValueError, KeyError, IndexError):
            await interaction.response.send_message("Duration must look like `30m`, `2h`, `3d`, or `1w`.", ephemeral=True)
            return

        try:
            await member.add_roles(role, reason=f"Temp role by {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("I can't assign that role (role hierarchy).", ephemeral=True)
            return

        expires_at = datetime.datetime.utcnow() + delta
        await db.add_temprole(interaction.guild_id, member.id, role.id, expires_at.isoformat())
        await interaction.response.send_message(
            f"Gave {member.mention} **{role.name}** until <t:{int(expires_at.timestamp())}:R>."
        )

    @tasks.loop(minutes=1)
    async def check_expiries(self):
        due = await db.get_due_temproles(datetime.datetime.utcnow().isoformat())
        for row in due:
            guild = self.bot.get_guild(row["guild_id"])
            if not guild:
                await db.remove_temprole_row(row["id"])
                continue
            member = guild.get_member(row["user_id"])
            role = guild.get_role(row["role_id"])
            if member and role and role in member.roles:
                try:
                    await member.remove_roles(role, reason="Temp role expired")
                except discord.Forbidden:
                    pass
            await db.remove_temprole_row(row["id"])

    @check_expiries.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(TempRoles(bot))
