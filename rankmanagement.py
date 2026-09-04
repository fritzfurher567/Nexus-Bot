"""
cogs/rankmanagement.py
Rank hierarchy and divisions (ranking/transfer system, adapted
to work purely with Discord roles rather than the Roblox group API, so it
works for any server — not just ones with a linked Roblox group).

- Admins define an ordered list of ranks, each tied to a Discord role
- /promote moves a member up one rank, /demote moves them down one,
  /setrank jumps them straight to a specific rank
- Divisions are a separate, non-hierarchical grouping (e.g. "Alpha Squad",
  "Logistics") — /transfer moves a member between them
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


def current_rank(member: discord.Member, ranks: list) -> dict | None:
    """Return the highest-order rank the member currently holds, or None."""
    held = [r for r in ranks if r["role_id"] in {role.id for role in member.roles}]
    return max(held, key=lambda r: r["rank_order"]) if held else None


class RankManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- RANK CONFIG ----------
    @app_commands.command(name="rank-add", description="Add a rank to the hierarchy (or update it if it already exists).")
    @app_commands.describe(rank_name="Name of the rank (e.g. 'Private')", role="Role tied to this rank", order="Position in the hierarchy — higher number = higher rank")
    @app_commands.checks.has_permissions(administrator=True)
    async def rank_add(self, interaction: discord.Interaction, rank_name: str, role: discord.Role, order: int):
        await db.add_rank(interaction.guild.id, rank_name, role.id, order)
        await interaction.response.send_message(embed=base_embed("Rank Added", f"**{rank_name}** ({role.mention}) set at order **{order}**.", COLOR_SUCCESS))

    @app_commands.command(name="rank-remove", description="Remove a rank from the hierarchy.")
    @app_commands.describe(rank_name="Name of the rank to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def rank_remove(self, interaction: discord.Interaction, rank_name: str):
        success = await db.remove_rank(interaction.guild.id, rank_name)
        if success:
            await interaction.response.send_message(embed=base_embed("Rank Removed", f"**{rank_name}** was removed from the hierarchy.", COLOR_SUCCESS))
        else:
            await interaction.response.send_message(embed=base_embed("Not Found", f"No rank called **{rank_name}**.", COLOR_ERROR), ephemeral=True)

    @app_commands.command(name="rank-list", description="Show the server's rank hierarchy.")
    async def rank_list(self, interaction: discord.Interaction):
        ranks = await db.get_ranks(interaction.guild.id)
        if not ranks:
            return await interaction.response.send_message(embed=base_embed("Rank Hierarchy", "No ranks configured yet. Use `/rank-add` to build one.", COLOR_INFO))
        lines = [f"**{i + 1}.** {r['rank_name']} — <@&{r['role_id']}>" for i, r in enumerate(reversed(ranks))]
        await interaction.response.send_message(embed=base_embed("📊 Rank Hierarchy (highest to lowest)", "\n".join(lines), COLOR_INFO))

    # ---------- PROMOTE / DEMOTE / SETRANK ----------
    @app_commands.command(name="promote", description="Promote a member to the next rank up.")
    @app_commands.describe(member="The member to promote")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def promote(self, interaction: discord.Interaction, member: discord.Member):
        ranks = await db.get_ranks(interaction.guild.id)
        if not ranks:
            return await interaction.response.send_message(embed=base_embed("No Ranks Configured", "Set up the hierarchy with `/rank-add` first.", COLOR_ERROR), ephemeral=True)

        present = current_rank(member, ranks)
        if present is None:
            target = ranks[0]  # entry-level rank
        else:
            higher = [r for r in ranks if r["rank_order"] > present["rank_order"]]
            if not higher:
                return await interaction.response.send_message(embed=base_embed("Already Top Rank", f"{member.mention} is already at the highest rank.", COLOR_INFO), ephemeral=True)
            target = min(higher, key=lambda r: r["rank_order"])

        old_role = interaction.guild.get_role(present["role_id"]) if present else None
        new_role = interaction.guild.get_role(target["role_id"])
        if old_role and old_role in member.roles:
            await member.remove_roles(old_role, reason=f"Promoted by {interaction.user}")
        if new_role:
            await member.add_roles(new_role, reason=f"Promoted by {interaction.user}")

        await interaction.response.send_message(embed=base_embed("⬆️ Promoted", f"{member.mention} was promoted to **{target['rank_name']}** by {interaction.user.mention}.", COLOR_SUCCESS))

    @app_commands.command(name="demote", description="Demote a member to the next rank down.")
    @app_commands.describe(member="The member to demote")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def demote(self, interaction: discord.Interaction, member: discord.Member):
        ranks = await db.get_ranks(interaction.guild.id)
        if not ranks:
            return await interaction.response.send_message(embed=base_embed("No Ranks Configured", "Set up the hierarchy with `/rank-add` first.", COLOR_ERROR), ephemeral=True)

        present = current_rank(member, ranks)
        if present is None:
            return await interaction.response.send_message(embed=base_embed("No Rank Held", f"{member.mention} doesn't currently hold a rank.", COLOR_INFO), ephemeral=True)

        lower = [r for r in ranks if r["rank_order"] < present["rank_order"]]
        if not lower:
            return await interaction.response.send_message(embed=base_embed("Already Lowest Rank", f"{member.mention} is already at the lowest rank. Use `/discharge` to remove them entirely.", COLOR_INFO), ephemeral=True)
        target = max(lower, key=lambda r: r["rank_order"])

        old_role = interaction.guild.get_role(present["role_id"])
        new_role = interaction.guild.get_role(target["role_id"])
        if old_role and old_role in member.roles:
            await member.remove_roles(old_role, reason=f"Demoted by {interaction.user}")
        if new_role:
            await member.add_roles(new_role, reason=f"Demoted by {interaction.user}")

        await interaction.response.send_message(embed=base_embed("⬇️ Demoted", f"{member.mention} was demoted to **{target['rank_name']}** by {interaction.user.mention}.", COLOR_ERROR))

    @app_commands.command(name="setrank", description="Set a member directly to a specific rank.")
    @app_commands.describe(member="The member to rank", rank_name="The exact rank name (see /rank-list)")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def setrank(self, interaction: discord.Interaction, member: discord.Member, rank_name: str):
        ranks = await db.get_ranks(interaction.guild.id)
        target = next((r for r in ranks if r["rank_name"].lower() == rank_name.lower()), None)
        if target is None:
            return await interaction.response.send_message(embed=base_embed("Rank Not Found", f"No rank called **{rank_name}**. Check `/rank-list`.", COLOR_ERROR), ephemeral=True)

        present = current_rank(member, ranks)
        old_role = interaction.guild.get_role(present["role_id"]) if present else None
        new_role = interaction.guild.get_role(target["role_id"])

        if old_role and old_role in member.roles:
            await member.remove_roles(old_role, reason=f"Rank set by {interaction.user}")
        if new_role:
            await member.add_roles(new_role, reason=f"Rank set by {interaction.user}")

        await interaction.response.send_message(embed=base_embed("Rank Set", f"{member.mention} is now **{target['rank_name']}**.", COLOR_SUCCESS))

    # ---------- DIVISIONS / TRANSFER ----------
    @app_commands.command(name="division-add", description="Add a division (a non-hierarchical group, e.g. a squad or team).")
    @app_commands.describe(division_name="Name of the division", role="Role tied to this division")
    @app_commands.checks.has_permissions(administrator=True)
    async def division_add(self, interaction: discord.Interaction, division_name: str, role: discord.Role):
        await db.add_division(interaction.guild.id, division_name, role.id)
        await interaction.response.send_message(embed=base_embed("Division Added", f"**{division_name}** ({role.mention}) is now available for `/transfer`.", COLOR_SUCCESS))

    @app_commands.command(name="division-list", description="List all configured divisions.")
    async def division_list(self, interaction: discord.Interaction):
        divisions = await db.get_divisions(interaction.guild.id)
        if not divisions:
            return await interaction.response.send_message(embed=base_embed("Divisions", "None configured yet.", COLOR_INFO))
        lines = [f"**{d['division_name']}** — <@&{d['role_id']}>" for d in divisions]
        await interaction.response.send_message(embed=base_embed("🗂️ Divisions", "\n".join(lines), COLOR_INFO))

    @app_commands.command(name="transfer", description="Transfer a member to a different division.")
    @app_commands.describe(member="The member to transfer", division_name="The division to move them to")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def transfer(self, interaction: discord.Interaction, member: discord.Member, division_name: str):
        divisions = await db.get_divisions(interaction.guild.id)
        target = next((d for d in divisions if d["division_name"].lower() == division_name.lower()), None)
        if target is None:
            return await interaction.response.send_message(embed=base_embed("Division Not Found", f"No division called **{division_name}**. Check `/division-list`.", COLOR_ERROR), ephemeral=True)

        # Remove any other division roles the member currently holds
        division_role_ids = {d["role_id"] for d in divisions}
        roles_to_remove = [role for role in member.roles if role.id in division_role_ids]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Transferred by {interaction.user}")

        new_role = interaction.guild.get_role(target["role_id"])
        if new_role:
            await member.add_roles(new_role, reason=f"Transferred by {interaction.user}")

        await interaction.response.send_message(embed=base_embed("🔄 Transferred", f"{member.mention} was transferred to **{target['division_name']}** by {interaction.user.mention}.", COLOR_SUCCESS))

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(embed=base_embed("Missing Permissions", "You don't have permission to use this command.", COLOR_ERROR), ephemeral=True)
        else:
            await interaction.response.send_message(embed=base_embed("Error", f"Something went wrong: `{error}`", COLOR_ERROR), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RankManagement(bot))
