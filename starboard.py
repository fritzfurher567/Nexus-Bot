"""
starboard.py
Messages that collect enough of a chosen emoji reaction get cross-posted
to a starboard channel.
"""
import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="starboard-setup", description="[Admin] Configure the starboard")
    @app_commands.checks.has_permissions(administrator=True)
    async def starboard_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, threshold: int = 3, emoji: str = "⭐"):
        await db.update_starboard_config(interaction.guild_id, channel_id=channel.id, threshold=threshold, emoji=emoji)
        await interaction.response.send_message(
            f"Starboard set to {channel.mention}, triggers at {threshold}x {emoji}.", ephemeral=True
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id:
            return

        config = await db.get_starboard_config(payload.guild_id)
        if not config["channel_id"]:
            return
        if str(payload.emoji) != config["emoji"]:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        message = await channel.fetch_message(payload.message_id)

        count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == config["emoji"]:
                count = reaction.count
                break

        if count < config["threshold"]:
            return

        board_channel = guild.get_channel(config["channel_id"])
        if not board_channel:
            return

        existing = await db.get_starboard_post(message.id)
        embed = discord.Embed(description=message.content, color=discord.Color.gold(), timestamp=message.created_at)
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        embed.add_field(name="Source", value=f"[Jump to message]({message.jump_url})")

        if existing:
            try:
                board_msg = await board_channel.fetch_message(existing["board_message_id"])
                await board_msg.edit(content=f"{config['emoji']} **{count}** | {channel.mention}", embed=embed)
            except discord.NotFound:
                pass
        else:
            board_msg = await board_channel.send(content=f"{config['emoji']} **{count}** | {channel.mention}", embed=embed)
            await db.add_starboard_post(message.id, payload.guild_id, board_msg.id)


async def setup(bot):
    await bot.add_cog(Starboard(bot))
