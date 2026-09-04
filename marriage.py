"""
marriage.py
Fun server marriage system.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class MarriageProposalView(discord.ui.View):
    def __init__(self, proposer: discord.Member, target: discord.Member):
        super().__init__(timeout=60)
        self.proposer = proposer
        self.target = target

    @discord.ui.button(label="Accept 💍", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("This proposal isn't for you.", ephemeral=True)
            return
        await db.create_marriage(interaction.guild_id, self.proposer.id, self.target.id, datetime.datetime.utcnow().isoformat())
        await interaction.response.edit_message(content=f"💍 {self.proposer.mention} and {self.target.mention} are now married!", view=None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("This proposal isn't for you.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"{self.target.mention} declined the proposal. 💔", view=None)


class Marriage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="marry", description="Propose marriage to another member")
    async def marry(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You can't marry yourself.", ephemeral=True)
            return
        existing = await db.get_marriage(interaction.guild_id, interaction.user.id)
        if existing:
            await interaction.response.send_message("You're already married. Use `/divorce` first.", ephemeral=True)
            return
        target_existing = await db.get_marriage(interaction.guild_id, member.id)
        if target_existing:
            await interaction.response.send_message(f"{member.display_name} is already married.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"💍 {interaction.user.mention} has proposed to {member.mention}!",
            view=MarriageProposalView(interaction.user, member),
        )

    @app_commands.command(name="divorce", description="End your marriage")
    async def divorce(self, interaction: discord.Interaction):
        existing = await db.get_marriage(interaction.guild_id, interaction.user.id)
        if not existing:
            await interaction.response.send_message("You're not married.", ephemeral=True)
            return
        await db.end_marriage(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message("💔 You're now divorced.")

    @app_commands.command(name="marriage-info", description="Check a member's marriage status")
    async def marriage_info(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        marriage = await db.get_marriage(interaction.guild_id, member.id)
        if not marriage:
            await interaction.response.send_message(f"{member.display_name} isn't married.", ephemeral=True)
            return
        partner_id = marriage["user2_id"] if marriage["user1_id"] == member.id else marriage["user1_id"]
        await interaction.response.send_message(f"💍 {member.mention} is married to <@{partner_id}>.")


async def setup(bot):
    await bot.add_cog(Marriage(bot))
