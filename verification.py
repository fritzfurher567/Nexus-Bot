"""
verification.py
Button + math-captcha verification gate for new members. Post a panel in
a locked-down welcome channel; members click "Verify", solve a simple
math problem in a modal, and get the verified role on a correct answer.
Combines with Honeypot for anti-raid: real members verify normally,
raid bots either fail the captcha or wander into the honeypot instead.
"""
import random

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class VerifyModal(discord.ui.Modal, title="Verification"):
    def __init__(self, a: int, b: int, verified_role_id: int):
        super().__init__()
        self.answer = a + b
        self.verified_role_id = verified_role_id
        self.response_field = discord.ui.TextInput(
            label=f"What is {a} + {b}?", placeholder="Type the number", max_length=6, required=True
        )
        self.add_item(self.response_field)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            given = int(str(self.response_field.value).strip())
        except ValueError:
            await interaction.response.send_message("That's not a number — try again with `/verify` again... err, click Verify again.", ephemeral=True)
            return

        if given != self.answer:
            await interaction.response.send_message("Incorrect answer. Click Verify to try again.", ephemeral=True)
            return

        role = interaction.guild.get_role(self.verified_role_id)
        if not role:
            await interaction.response.send_message("Verified role is misconfigured — tell an admin.", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(role, reason="Passed verification captcha")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to give you the verified role.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Verified! Welcome in.", ephemeral=True)


class VerifyPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="verification:verify")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await db.get_verification_config(interaction.guild_id)
        if not config["verified_role_id"]:
            await interaction.response.send_message("Verification isn't set up yet.", ephemeral=True)
            return

        role = interaction.guild.get_role(config["verified_role_id"])
        if role and role in interaction.user.roles:
            await interaction.response.send_message("You're already verified.", ephemeral=True)
            return

        a, b = random.randint(1, 20), random.randint(1, 20)
        await interaction.response.send_modal(VerifyModal(a, b, config["verified_role_id"]))


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(VerifyPanelView())

    @app_commands.command(name="verify-setup", description="[Admin] Post the verification panel and set the verified role")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_setup(self, interaction: discord.Interaction, verified_role: discord.Role):
        await db.set_verification_config(interaction.guild_id, interaction.channel_id, verified_role.id)

        embed = discord.Embed(
            title="👋 Welcome — Verify to Continue",
            description="Click **Verify** below and solve the quick math check to get access to the rest of the server.",
            color=discord.Color.green(),
        )
        await interaction.channel.send(embed=embed, view=VerifyPanelView())
        await interaction.response.send_message(
            f"Verification panel posted. New members get {verified_role.mention} once they pass.", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Verification(bot))
