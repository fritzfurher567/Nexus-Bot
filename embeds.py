"""
cogs/embeds.py
Lets staff build and send custom embeds using a pop-up modal
(so descriptions can be multi-line, unlike normal slash command text boxes).
"""

import discord
from discord import app_commands
from discord.ext import commands

from config import COLOR_INFO, BOT_CREDIT


class EmbedModal(discord.ui.Modal, title="Create an Embed"):
    embed_title = discord.ui.TextInput(label="Title", max_length=256, required=False, placeholder="Embed title")
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=4000, required=True, placeholder="Main embed text")
    color_hex = discord.ui.TextInput(label="Color (hex, e.g. 5865F2)", max_length=6, required=False, placeholder="5865F2")
    footer = discord.ui.TextInput(label="Footer text", max_length=256, required=False, placeholder="Optional footer")
    image_url = discord.ui.TextInput(label="Image URL", max_length=500, required=False, placeholder="Optional image URL")

    def __init__(self, target_channel: discord.TextChannel):
        super().__init__()
        self.target_channel = target_channel

    async def on_submit(self, interaction: discord.Interaction):
        color = COLOR_INFO
        if self.color_hex.value:
            try:
                color = int(self.color_hex.value.strip("#"), 16)
            except ValueError:
                pass

        embed = discord.Embed(
            title=self.embed_title.value or None,
            description=self.description.value,
            color=color,
        )
        if self.image_url.value:
            embed.set_image(url=self.image_url.value)

        footer_text = self.footer.value if self.footer.value else BOT_CREDIT
        embed.set_footer(text=footer_text)

        await self.target_channel.send(embed=embed)
        await interaction.response.send_message(f"Embed sent to {self.target_channel.mention}.", ephemeral=True)


class Embeds(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Build and send a custom embed to a channel.")
    @app_commands.describe(channel="Channel to send the embed to (defaults to this channel)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        target = channel or interaction.channel
        await interaction.response.send_modal(EmbedModal(target))

    @app_commands.command(name="say", description="Make the bot say something in a channel (plain text).")
    @app_commands.describe(message="What the bot should say", channel="Channel to send to (defaults to this channel)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def say(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
        target = channel or interaction.channel
        await target.send(message)
        await interaction.response.send_message(f"Message sent to {target.mention}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))
