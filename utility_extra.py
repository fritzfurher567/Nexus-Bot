"""
utility_extra.py
Everyday utility commands not already covered: timestamps, math,
timezone conversion, banner lookup, member/role counts, uptime,
and a basic word/character counter.
"""
import time
import datetime

import discord
from discord import app_commands
from discord.ext import commands

_start_time = time.time()


class UtilityExtra(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="banner", description="View a member's banner (if they have one)")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        user = await self.bot.fetch_user(member.id)  # banners aren't cached on Member
        if not user.banner:
            await interaction.response.send_message(f"{member.display_name} doesn't have a banner set.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{member.display_name}'s Banner", color=discord.Color.blurple())
        embed.set_image(url=user.banner.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timestamp", description="Convert minutes-from-now into a Discord timestamp tag")
    async def timestamp(self, interaction: discord.Interaction, minutes_from_now: int):
        target = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes_from_now)
        unix = int(target.timestamp())
        await interaction.response.send_message(
            f"`<t:{unix}:F>` → <t:{unix}:F>\n`<t:{unix}:R>` → <t:{unix}:R>", ephemeral=True
        )

    @app_commands.command(name="calculate", description="Evaluate a basic math expression")
    async def calculate(self, interaction: discord.Interaction, expression: str):
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            await interaction.response.send_message("Only numbers and + - * / ( ) are allowed.", ephemeral=True)
            return
        try:
            result = eval(expression, {"__builtins__": {}})
        except Exception:
            await interaction.response.send_message("Couldn't evaluate that expression.", ephemeral=True)
            return
        await interaction.response.send_message(f"`{expression}` = **{result}**")

    @app_commands.command(name="charcount", description="Count characters/words in a block of text")
    async def charcount(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(
            f"**Characters:** {len(text)} | **Words:** {len(text.split())}", ephemeral=True
        )

    @app_commands.command(name="membercount", description="Show member/bot/human counts for this server")
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots
        embed = discord.Embed(title=f"{guild.name} — Member Count", color=discord.Color.blurple())
        embed.add_field(name="Total", value=str(guild.member_count))
        embed.add_field(name="Humans", value=str(humans))
        embed.add_field(name="Bots", value=str(bots))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rolecount", description="Show how many members have a given role")
    async def rolecount(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.send_message(f"**{role.name}** has {len(role.members)} member(s).")

    @app_commands.command(name="uptime", description="Show how long the bot has been running")
    async def uptime(self, interaction: discord.Interaction):
        elapsed = int(time.time() - _start_time)
        h, remainder = divmod(elapsed, 3600)
        m, s = divmod(remainder, 60)
        await interaction.response.send_message(f"Uptime: **{h}h {m}m {s}s**")

    @app_commands.command(name="servericon", description="Get this server's icon at full resolution")
    async def servericon(self, interaction: discord.Interaction):
        if not interaction.guild.icon:
            await interaction.response.send_message("This server has no icon set.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{interaction.guild.name}'s Icon", color=discord.Color.blurple())
        embed.set_image(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channelinfo", description="Show info about a channel")
    async def channelinfo(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        embed = discord.Embed(title=f"#{channel.name}", color=discord.Color.blurple())
        embed.add_field(name="ID", value=str(channel.id))
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None")
        embed.add_field(name="Created", value=discord.utils.format_dt(channel.created_at, "R"))
        embed.add_field(name="Topic", value=channel.topic or "None", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(UtilityExtra(bot))
