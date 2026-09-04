"""
invites.py
Tracks which invite a member used to join, and a leaderboard of who's
brought in the most people.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # cache current invite counts per guild so we can diff on join
        self.invite_cache: dict[int, dict[str, int]] = {}
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invite_cache[guild.id] = {inv.code: inv.uses or 0 for inv in invites}
            except discord.Forbidden:
                self.invite_cache[guild.id] = {}

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        self.invite_cache.setdefault(invite.guild.id, {})[invite.code] = invite.uses or 0

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        try:
            current = await guild.invites()
        except discord.Forbidden:
            return

        before = self.invite_cache.get(guild.id, {})
        used_invite = None
        for inv in current:
            if inv.uses and inv.uses > before.get(inv.code, 0):
                used_invite = inv
                break

        self.invite_cache[guild.id] = {inv.code: inv.uses or 0 for inv in current}

        if used_invite:
            await db.upsert_invite_use(guild.id, used_invite.code, used_invite.inviter.id if used_invite.inviter else None, used_invite.uses or 0)
            await db.record_join_via(guild.id, member.id, used_invite.code, used_invite.inviter.id if used_invite.inviter else None)

    @app_commands.command(name="invites", description="See your (or someone's) invite count")
    async def invites(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        rows = await db.get_invite_uses(interaction.guild_id)
        total = sum(r["uses"] for r in rows if r["inviter_id"] == member.id)
        await interaction.response.send_message(f"{member.mention} has **{total}** invite(s).")

    @app_commands.command(name="invite-leaderboard", description="Top inviters in this server")
    async def invite_leaderboard(self, interaction: discord.Interaction):
        rows = await db.get_inviter_leaderboard(interaction.guild_id)
        lines = []
        for i, r in enumerate(rows, 1):
            if not r["inviter_id"]:
                continue
            member = interaction.guild.get_member(r["inviter_id"])
            name = member.display_name if member else f"User {r['inviter_id']}"
            lines.append(f"**{i}.** {name} — {r['total']} invites")
        embed = discord.Embed(title="📨 Invite Leaderboard", description="\n".join(lines) or "No data yet.", color=discord.Color.teal())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Invites(bot))
