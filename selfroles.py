"""
selfroles.py
Dropdown-menu self-roles — distinct from Reaction Roles.py (which is
emoji-based). Admins whitelist which roles are self-assignable, then
members pick from a select menu instead of reacting.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database as db


class SelfRoleSelect(discord.ui.Select):
    def __init__(self, roles: list[discord.Role]):
        options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles[:25]]
        super().__init__(placeholder="Choose your roles...", options=options, min_values=0, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        selected_ids = {int(v) for v in self.values}
        all_role_ids = {int(o.value) for o in self.options}
        member = interaction.user

        added, removed = [], []
        for role_id in all_role_ids:
            role = interaction.guild.get_role(role_id)
            if not role:
                continue
            if role_id in selected_ids and role not in member.roles:
                await member.add_roles(role)
                added.append(role.name)
            elif role_id not in selected_ids and role in member.roles:
                await member.remove_roles(role)
                removed.append(role.name)

        msg = []
        if added:
            msg.append(f"Added: {', '.join(added)}")
        if removed:
            msg.append(f"Removed: {', '.join(removed)}")
        await interaction.response.send_message("\n".join(msg) or "No changes.", ephemeral=True)


class SelfRoleView(discord.ui.View):
    def __init__(self, roles: list[discord.Role]):
        super().__init__(timeout=None)
        self.add_item(SelfRoleSelect(roles))


class SelfRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="selfrole-add", description="[Admin] Add a role to the self-assignable list")
    @app_commands.checks.has_permissions(administrator=True)
    async def selfrole_add(self, interaction: discord.Interaction, role: discord.Role):
        await db.add_selfrole(interaction.guild_id, role.id)
        await interaction.response.send_message(f"Added **{role.name}** to self-roles.", ephemeral=True)

    @app_commands.command(name="selfrole-remove", description="[Admin] Remove a role from the self-assignable list")
    @app_commands.checks.has_permissions(administrator=True)
    async def selfrole_remove(self, interaction: discord.Interaction, role: discord.Role):
        removed = await db.remove_selfrole(interaction.guild_id, role.id)
        if removed:
            await interaction.response.send_message(f"Removed **{role.name}** from self-roles.", ephemeral=True)
        else:
            await interaction.response.send_message("That role wasn't on the self-role list.", ephemeral=True)

    @app_commands.command(name="selfrole-panel", description="Post the self-role picker menu")
    async def selfrole_panel(self, interaction: discord.Interaction):
        role_ids = await db.get_selfroles(interaction.guild_id)
        roles = [interaction.guild.get_role(rid) for rid in role_ids]
        roles = [r for r in roles if r is not None]
        if not roles:
            await interaction.response.send_message("No self-roles configured yet.", ephemeral=True)
            return
        embed = discord.Embed(title="🎭 Pick Your Roles", description="Use the dropdown below.", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=SelfRoleView(roles))


async def setup(bot):
    await bot.add_cog(SelfRoles(bot))
