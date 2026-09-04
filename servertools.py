"""
servertools.py
Server-management helpers: emoji add/remove, channel cloning, category
creation, sticker listing.
"""
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands


class ServerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addemoji", description="[Admin] Add an emoji from an image URL")
    @app_commands.checks.has_permissions(manage_emojis_and_stickers=True)
    async def addemoji(self, interaction: discord.Interaction, name: str, image_url: str):
        await interaction.response.defer(ephemeral=True)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Couldn't fetch that image.", ephemeral=True)
                        return
                    image_bytes = await resp.read()
            emoji = await interaction.guild.create_custom_emoji(name=name, image=image_bytes)
            await interaction.followup.send(f"Added emoji {emoji}", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"Failed to add emoji: {e}", ephemeral=True)

    @app_commands.command(name="removeemoji", description="[Admin] Remove a custom emoji")
    @app_commands.checks.has_permissions(manage_emojis_and_stickers=True)
    async def removeemoji(self, interaction: discord.Interaction, emoji_name: str):
        emoji = discord.utils.get(interaction.guild.emojis, name=emoji_name)
        if not emoji:
            await interaction.response.send_message("No emoji with that name.", ephemeral=True)
            return
        await emoji.delete()
        await interaction.response.send_message(f"Removed emoji `{emoji_name}`.", ephemeral=True)

    @app_commands.command(name="categorycreate", description="[Admin] Create a new channel category")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def categorycreate(self, interaction: discord.Interaction, name: str):
        category = await interaction.guild.create_category(name)
        await interaction.response.send_message(f"Created category **{category.name}**.", ephemeral=True)

    @app_commands.command(name="channelclone", description="[Admin] Clone a channel (structure only, no messages)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channelclone(self, interaction: discord.Interaction, channel: discord.TextChannel, new_name: str = None):
        clone = await channel.clone(name=new_name)
        await interaction.response.send_message(f"Cloned {channel.mention} as {clone.mention}.", ephemeral=True)

    @app_commands.command(name="stickerlist", description="List this server's custom stickers")
    async def stickerlist(self, interaction: discord.Interaction):
        stickers = interaction.guild.stickers
        if not stickers:
            await interaction.response.send_message("This server has no custom stickers.", ephemeral=True)
            return
        await interaction.response.send_message(", ".join(s.name for s in stickers))


async def setup(bot):
    await bot.add_cog(ServerTools(bot))
