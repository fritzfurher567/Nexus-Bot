"""
cogs/reactionroles.py
Emoji-based reaction roles:
- Admin links an emoji on an existing message to a role
- The bot adds that reaction to the message automatically
- Users get/lose the role by adding/removing the reaction
"""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, BOT_CREDIT


class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reactionrole-add", description="Link an emoji on a message to a role.")
    @app_commands.describe(
        message_id="The ID of the message to attach the reaction to (right-click → Copy Message ID)",
        emoji="The emoji to use",
        role="The role to grant when someone reacts",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_add(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        try:
            target_message = None
            for channel in interaction.guild.text_channels:
                try:
                    target_message = await channel.fetch_message(int(message_id))
                    break
                except (discord.NotFound, discord.Forbidden):
                    continue
        except ValueError:
            return await interaction.response.send_message("That doesn't look like a valid message ID.", ephemeral=True)

        if target_message is None:
            return await interaction.response.send_message("Couldn't find a message with that ID in this server.", ephemeral=True)

        try:
            await target_message.add_reaction(emoji)
        except discord.HTTPException:
            return await interaction.response.send_message("That emoji isn't valid or I can't use it.", ephemeral=True)

        await db.add_reaction_role(interaction.guild.id, target_message.id, emoji, role.id)

        embed = discord.Embed(
            title="Reaction Role Added",
            description=f"Reacting with {emoji} on [that message]({target_message.jump_url}) will now give **{role.name}**.",
            color=COLOR_SUCCESS
        )
        embed.set_footer(text=BOT_CREDIT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reactionrole-remove", description="Remove a reaction role link.")
    @app_commands.describe(message_id="The message ID the reaction role is on", emoji="The emoji to unlink")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole_remove(self, interaction: discord.Interaction, message_id: str, emoji: str):
        try:
            success = await db.remove_reaction_role(int(message_id), emoji)
        except ValueError:
            return await interaction.response.send_message("That doesn't look like a valid message ID.", ephemeral=True)

        if success:
            embed = discord.Embed(title="Reaction Role Removed", description=f"{emoji} no longer grants a role on that message.", color=COLOR_SUCCESS)
        else:
            embed = discord.Embed(title="Not Found", description="No reaction role matched that message and emoji.", color=COLOR_ERROR)
        embed.set_footer(text=BOT_CREDIT)
        await interaction.response.send_message(embed=embed, ephemeral=not success)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member is None or payload.member.bot:
            return
        role_id = await db.get_reaction_role(payload.message_id, str(payload.emoji))
        if role_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(role_id) if guild else None
        if role:
            try:
                await payload.member.add_roles(role, reason="Reaction role")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        role_id = await db.get_reaction_role(payload.message_id, str(payload.emoji))
        if role_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        if member and role and not member.bot:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
