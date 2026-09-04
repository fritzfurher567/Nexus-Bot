"""
activity.py
Tracks voice-channel time and message counts per member, with
leaderboards for both.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        await db.increment_message_count(message.guild.id, message.author.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        now = datetime.datetime.utcnow().isoformat()

        # joined a voice channel (wasn't in one before)
        if before.channel is None and after.channel is not None:
            await db.start_voice_session(member.guild.id, member.id, now)

        # left voice entirely
        elif before.channel is not None and after.channel is None:
            start = await db.get_voice_session_start(member.guild.id, member.id)
            if start:
                elapsed = int((datetime.datetime.utcnow() - datetime.datetime.fromisoformat(start)).total_seconds())
                await db.end_voice_session(member.guild.id, member.id, elapsed)

    @app_commands.command(name="voice-leaderboard", description="Top voice-channel time in this server")
    async def voice_leaderboard(self, interaction: discord.Interaction):
        rows = await db.get_voice_leaderboard(interaction.guild_id)
        lines = []
        for i, r in enumerate(rows, 1):
            member = interaction.guild.get_member(r["user_id"])
            name = member.display_name if member else f"User {r['user_id']}"
            hours, remainder = divmod(r["seconds"], 3600)
            minutes = remainder // 60
            lines.append(f"**{i}.** {name} — {hours}h {minutes}m")
        embed = discord.Embed(title="🎙️ Voice Leaderboard", description="\n".join(lines) or "No data yet.", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="messages-leaderboard", description="Most active chatters in this server")
    async def messages_leaderboard(self, interaction: discord.Interaction):
        rows = await db.get_message_leaderboard(interaction.guild_id)
        lines = []
        for i, r in enumerate(rows, 1):
            member = interaction.guild.get_member(r["user_id"])
            name = member.display_name if member else f"User {r['user_id']}"
            lines.append(f"**{i}.** {name} — {r['count']:,} messages")
        embed = discord.Embed(title="💬 Message Leaderboard", description="\n".join(lines) or "No data yet.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Activity(bot))
