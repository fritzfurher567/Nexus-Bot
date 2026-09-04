"""
cogs/welcome.py
Handles welcome/goodbye messages in a channel, plus optional DMs to the
member when they join or leave. Messages support placeholders:
  {user}         -> mention of the member
  {username}     -> plain name of the member
  {server}       -> server name
  {membercount}  -> current member count
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT


def format_message(template: str, member: discord.Member, guild: discord.Guild) -> str:
    return (
        template
        .replace("{user}", member.mention)
        .replace("{username}", str(member.name))
        .replace("{server}", guild.name)
        .replace("{membercount}", str(guild.member_count))
    )


def base_embed(title: str, description: str, color: int) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color,
                           timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = await db.get_guild_config(member.guild.id)

        channel_id = config.get("welcome_channel")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                text = format_message(config.get("welcome_message"), member, member.guild)
                embed = base_embed("👋 Welcome!", text, COLOR_SUCCESS)
                embed.set_thumbnail(url=member.display_avatar.url)
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        if config.get("dm_on_join"):
            text = format_message(config.get("dm_on_join_message"), member, member.guild)
            try:
                await member.send(embed=base_embed(f"Welcome to {member.guild.name}!", text, COLOR_SUCCESS))
            except discord.Forbidden:
                pass  # user has DMs closed

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = await db.get_guild_config(member.guild.id)

        channel_id = config.get("goodbye_channel")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                text = format_message(config.get("goodbye_message"), member, member.guild)
                embed = base_embed("👋 Goodbye", text, COLOR_ERROR)
                embed.set_thumbnail(url=member.display_avatar.url)
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        if config.get("dm_on_leave"):
            text = format_message(config.get("dm_on_leave_message"), member, member.guild)
            try:
                await member.send(embed=base_embed(f"Leaving {member.guild.name}", text, COLOR_INFO))
            except discord.Forbidden:
                pass  # bot and user no longer share a server, or DMs closed

    # ---------- CONFIG COMMANDS ----------
    @app_commands.command(name="welcome-setup", description="Set the channel and message for welcome announcements.")
    @app_commands.describe(channel="Channel to post welcome messages in", message="Use {user}, {username}, {server}, {membercount}")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str = None):
        kwargs = {"welcome_channel": channel.id}
        if message:
            kwargs["welcome_message"] = message
        await db.update_guild_config(interaction.guild.id, **kwargs)
        await interaction.response.send_message(embed=base_embed("Welcome Configured", f"Welcome messages will be posted in {channel.mention}.", COLOR_SUCCESS))

    @app_commands.command(name="goodbye-setup", description="Set the channel and message for goodbye announcements.")
    @app_commands.describe(channel="Channel to post goodbye messages in", message="Use {user}, {username}, {server}, {membercount}")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str = None):
        kwargs = {"goodbye_channel": channel.id}
        if message:
            kwargs["goodbye_message"] = message
        await db.update_guild_config(interaction.guild.id, **kwargs)
        await interaction.response.send_message(embed=base_embed("Goodbye Configured", f"Goodbye messages will be posted in {channel.mention}.", COLOR_SUCCESS))

    @app_commands.command(name="welcome-dm", description="Toggle sending a DM to new members when they join.")
    @app_commands.describe(enabled="Turn welcome DMs on or off", message="Use {user}, {username}, {server}, {membercount}")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_dm(self, interaction: discord.Interaction, enabled: bool, message: str = None):
        kwargs = {"dm_on_join": int(enabled)}
        if message:
            kwargs["dm_on_join_message"] = message
        await db.update_guild_config(interaction.guild.id, **kwargs)
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=base_embed("Join DM Updated", f"Join DMs are now **{state}**.", COLOR_SUCCESS))

    @app_commands.command(name="goodbye-dm", description="Toggle sending a DM to members when they leave.")
    @app_commands.describe(enabled="Turn leave DMs on or off", message="Use {user}, {username}, {server}, {membercount}")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_dm(self, interaction: discord.Interaction, enabled: bool, message: str = None):
        kwargs = {"dm_on_leave": int(enabled)}
        if message:
            kwargs["dm_on_leave_message"] = message
        await db.update_guild_config(interaction.guild.id, **kwargs)
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=base_embed("Leave DM Updated", f"Leave DMs are now **{state}**.", COLOR_SUCCESS))


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
