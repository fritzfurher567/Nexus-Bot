"""
cogs/discharge.py
Discharge system + desertion detection + background checks:
- /discharge removes a member's rank/division roles (and optionally kicks them),
  with a logged reason
- Desertion detection: if a ranked/divisioned member leaves the server on
  their own, it's automatically logged as a desertion
- /backgroundcheck pulls together everything the bot knows about a member —
  join date, rank, division, warnings, awards, verification, LOA status —
  into one report
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT


def base_embed(title: str, description: str, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


class Discharge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- DISCHARGE ----------
    @app_commands.command(name="discharge", description="Discharge a member — strips rank/division roles, with a logged reason.")
    @app_commands.describe(member="The member to discharge", reason="Reason for the discharge", kick="Also kick them from the server")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def discharge(self, interaction: discord.Interaction, member: discord.Member, reason: str, kick: bool = False):
        ranks = await db.get_ranks(interaction.guild.id)
        divisions = await db.get_divisions(interaction.guild.id)
        managed_role_ids = {r["role_id"] for r in ranks} | {d["role_id"] for d in divisions}

        roles_to_remove = [role for role in member.roles if role.id in managed_role_ids]
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason=f"Discharged by {interaction.user}: {reason}")
            except discord.Forbidden:
                pass

        timestamp = datetime.datetime.utcnow().isoformat()
        await db.add_discharge(interaction.guild.id, member.id, interaction.user.id, reason, False, timestamp)

        try:
            await member.send(embed=base_embed(f"You were discharged from {interaction.guild.name}", f"**Reason:** {reason}", COLOR_ERROR))
        except discord.Forbidden:
            pass

        if kick:
            try:
                await member.kick(reason=f"Discharged: {reason}")
            except discord.Forbidden:
                pass

        embed = base_embed("📋 Member Discharged", f"**{member}** was discharged by {interaction.user.mention}\n**Reason:** {reason}" + ("\n**Kicked:** Yes" if kick else ""), COLOR_ERROR)
        await interaction.response.send_message(embed=embed)

        config = await db.get_guild_config(interaction.guild.id)
        channel_id = config.get("discharge_channel")
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel and channel.id != interaction.channel.id:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    @app_commands.command(name="discharges", description="View a member's discharge history.")
    @app_commands.describe(member="The member to check")
    async def discharges(self, interaction: discord.Interaction, member: discord.Member):
        records = await db.get_discharges(interaction.guild.id, member.id)
        if not records:
            return await interaction.response.send_message(embed=base_embed("Discharge History", f"{member.mention} has no discharge history.", COLOR_SUCCESS))

        lines = []
        for r in records:
            tag = "🔍 Desertion" if r["is_desertion"] else "📋 Discharge"
            lines.append(f"{tag} — {r['reason']} (<t:{int(datetime.datetime.fromisoformat(r['timestamp']).timestamp())}:D>)")
        await interaction.response.send_message(embed=base_embed(f"Discharge History — {member}", "\n".join(lines), COLOR_INFO))

    @app_commands.command(name="discharge-channel", description="Set the channel where discharges and desertions are logged.")
    @app_commands.describe(channel="Channel for discharge/desertion logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def discharge_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.update_guild_config(interaction.guild.id, discharge_channel=channel.id)
        await interaction.response.send_message(embed=base_embed("Discharge Channel Set", f"Discharges and desertions will be logged to {channel.mention}.", COLOR_SUCCESS))

    # ---------- DESERTION DETECTION ----------
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ranks = await db.get_ranks(member.guild.id)
        divisions = await db.get_divisions(member.guild.id)
        managed_role_ids = {r["role_id"] for r in ranks} | {d["role_id"] for d in divisions}

        held_role_ids = {role.id for role in member.roles}
        if not held_role_ids.intersection(managed_role_ids):
            return  # they held no rank/division — nothing to flag

        timestamp = datetime.datetime.utcnow().isoformat()
        await db.add_discharge(member.guild.id, member.id, None, "Left the server while holding rank/division", True, timestamp)

        config = await db.get_guild_config(member.guild.id)
        channel_id = config.get("discharge_channel")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=base_embed(
                        "🔍 Desertion Detected",
                        f"**{member}** left the server while still holding a rank or division role.",
                        COLOR_ERROR
                    ))
                except discord.Forbidden:
                    pass

    @app_commands.command(name="desertions", description="Show recent desertions (members who left while ranked).")
    async def desertions(self, interaction: discord.Interaction):
        records = await db.get_recent_desertions(interaction.guild.id)
        if not records:
            return await interaction.response.send_message(embed=base_embed("Desertions", "No desertions logged.", COLOR_SUCCESS))
        lines = [f"<@{r['user_id']}> — <t:{int(datetime.datetime.fromisoformat(r['timestamp']).timestamp())}:R>" for r in records]
        await interaction.response.send_message(embed=base_embed("🔍 Recent Desertions", "\n".join(lines), COLOR_ERROR))

    # ---------- BACKGROUND CHECK ----------
    @app_commands.command(name="backgroundcheck", description="Pull together everything the bot knows about a member.")
    @app_commands.describe(member="The member to check")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def backgroundcheck(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        ranks = await db.get_ranks(interaction.guild.id)
        divisions = await db.get_divisions(interaction.guild.id)
        held_role_ids = {role.id for role in member.roles}

        rank_held = next((r["rank_name"] for r in ranks if r["role_id"] in held_role_ids), "None")
        division_held = next((d["division_name"] for d in divisions if d["role_id"] in held_role_ids), "None")

        warnings = await db.get_warnings(interaction.guild.id, member.id)
        awards = await db.get_awards(interaction.guild.id, member.id)
        discharges = await db.get_discharges(interaction.guild.id, member.id)
        roblox = await db.get_roblox_verification(interaction.guild.id, member.id)

        embed = base_embed(f"🛡️ Background Check — {member}", None, COLOR_INFO)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Roblox Account", value=roblox["roblox_username"] if roblox else "Not verified", inline=True)
        embed.add_field(name="Current Rank", value=rank_held, inline=True)
        embed.add_field(name="Division", value=division_held, inline=True)
        embed.add_field(name="Roles", value=str(len(member.roles) - 1), inline=True)
        embed.add_field(name="Warnings", value=str(len(warnings)), inline=True)
        embed.add_field(name="Awards", value=str(len(awards)), inline=True)
        embed.add_field(name="Past Discharges", value=str(len(discharges)), inline=True)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Discharge(bot))
