"""
cogs/leveling.py
XP and leveling system:
- Members earn XP for chatting, with a per-user cooldown to prevent spam
- /rank shows a member's level, XP, and progress to next level
- /leaderboard shows the top members by XP
- Admins can assign roles that get auto-granted at specific levels
- Level-up announcements post in a configurable channel (or the message channel by default)
"""

import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import (
    COLOR_SUCCESS, COLOR_INFO, BOT_CREDIT,
    XP_MIN_PER_MESSAGE, XP_MAX_PER_MESSAGE, XP_MESSAGE_COOLDOWN_SECONDS, xp_for_level,
)


def base_embed(title: str, description: str = None, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


def progress_bar(current: int, needed: int, length: int = 15) -> str:
    filled = int(length * (current / needed)) if needed else 0
    filled = max(0, min(length, filled))
    return "█" * filled + "░" * (length - filled)


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = await db.get_level_data(message.guild.id, message.author.id)
        now = datetime.datetime.utcnow()

        if data["last_xp_time"]:
            last_time = datetime.datetime.fromisoformat(data["last_xp_time"])
            if (now - last_time).total_seconds() < XP_MESSAGE_COOLDOWN_SECONDS:
                return  # still on cooldown, no XP this message

        gained = random.randint(XP_MIN_PER_MESSAGE, XP_MAX_PER_MESSAGE)
        new_xp = data["xp"] + gained
        new_level = data["level"]

        leveled_up = False
        while new_xp >= xp_for_level(new_level + 1):
            new_level += 1
            leveled_up = True

        await db.update_xp(message.guild.id, message.author.id, new_xp, new_level, now.isoformat())

        if leveled_up:
            await self._handle_level_up(message, new_level)

    async def _handle_level_up(self, message: discord.Message, new_level: int):
        config = await db.get_guild_config(message.guild.id)
        channel_id = config.get("levelup_channel")
        channel = message.guild.get_channel(channel_id) if channel_id else message.channel

        if channel:
            embed = base_embed(
                "🎉 Level Up!",
                f"{message.author.mention} just reached **Level {new_level}**!",
                COLOR_SUCCESS
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

        # Grant any role reward configured for this level
        level_roles = await db.get_level_roles(message.guild.id)
        for entry in level_roles:
            if entry["level"] == new_level:
                role = message.guild.get_role(entry["role_id"])
                if role:
                    try:
                        await message.author.add_roles(role, reason=f"Reached level {new_level}")
                    except discord.Forbidden:
                        pass

    @app_commands.command(name="rank", description="Show your (or another member's) level and XP.")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        data = await db.get_level_data(interaction.guild.id, member.id)
        level, xp = data["level"], data["xp"]

        current_floor = xp_for_level(level)
        next_needed = xp_for_level(level + 1)
        into_level = xp - current_floor
        span = next_needed - current_floor

        embed = base_embed(f"Rank — {member}")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Total XP", value=str(xp), inline=True)
        embed.add_field(
            name="Progress to Next Level",
            value=f"`{progress_bar(into_level, span)}`\n{into_level}/{span} XP",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the server's top members by XP.")
    async def leaderboard(self, interaction: discord.Interaction):
        top = await db.get_level_leaderboard(interaction.guild.id, limit=10)
        if not top:
            return await interaction.response.send_message(embed=base_embed("Leaderboard", "No XP data yet — start chatting!"))

        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, entry in enumerate(top):
            member = interaction.guild.get_member(entry["user_id"])
            name = member.mention if member else f"<@{entry['user_id']}>"
            prefix = medals[i] if i < 3 else f"**#{i + 1}**"
            lines.append(f"{prefix} {name} — Level {entry['level']} ({entry['xp']} XP)")

        await interaction.response.send_message(embed=base_embed("🏆 XP Leaderboard", "\n".join(lines)))

    @app_commands.command(name="setlevelrole", description="Set a role to be auto-granted at a specific level.")
    @app_commands.describe(level="The level that triggers this role", role="The role to grant")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlevelrole(self, interaction: discord.Interaction, level: app_commands.Range[int, 1, 1000], role: discord.Role):
        await db.set_level_role(interaction.guild.id, level, role.id)
        await interaction.response.send_message(
            embed=base_embed("Level Role Set", f"Members will now receive {role.mention} at **Level {level}**.", COLOR_SUCCESS)
        )

    @app_commands.command(name="removelevelrole", description="Remove a level-role reward.")
    @app_commands.describe(level="The level to remove the role reward from")
    @app_commands.checks.has_permissions(administrator=True)
    async def removelevelrole(self, interaction: discord.Interaction, level: int):
        success = await db.remove_level_role(interaction.guild.id, level)
        if success:
            await interaction.response.send_message(embed=base_embed("Level Role Removed", f"Removed the role reward for Level {level}.", COLOR_SUCCESS))
        else:
            await interaction.response.send_message(embed=base_embed("Not Found", f"No role reward was set for Level {level}.", COLOR_INFO), ephemeral=True)

    @app_commands.command(name="levelup-channel", description="Set the channel for level-up announcements.")
    @app_commands.describe(channel="Channel to post level-up messages in")
    @app_commands.checks.has_permissions(administrator=True)
    async def levelup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.update_guild_config(interaction.guild.id, levelup_channel=channel.id)
        await interaction.response.send_message(embed=base_embed("Level-Up Channel Set", f"Level-up announcements will post in {channel.mention}.", COLOR_SUCCESS))


async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
