"""
scheduling.py
Schedule a message to post later, and a live countdown timer.
"""
import asyncio
import datetime

import discord
from discord import app_commands
from discord.ext import commands


class Scheduling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="schedule-message", description="[Mod] Schedule a message to post in this channel after N minutes")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def schedule_message(self, interaction: discord.Interaction, minutes: int, content: str):
        if minutes <= 0 or minutes > 10080:
            await interaction.response.send_message("Minutes must be between 1 and 10080.", ephemeral=True)
            return
        await interaction.response.send_message(f"Scheduled — will post in {minutes} minute(s).", ephemeral=True)
        channel = interaction.channel
        await asyncio.sleep(minutes * 60)
        await channel.send(content)

    @app_commands.command(name="countdown", description="Post a live countdown timer")
    async def countdown(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 3, 60], title: str = "Countdown"):
        await interaction.response.send_message(f"⏳ **{title}** — {seconds}")
        msg = await interaction.original_response()
        for remaining in range(seconds - 1, 0, -1):
            await asyncio.sleep(1)
            try:
                await msg.edit(content=f"⏳ **{title}** — {remaining}")
            except discord.NotFound:
                return
        await asyncio.sleep(1)
        await msg.edit(content=f"🎉 **{title}** — Go!")


async def setup(bot):
    await bot.add_cog(Scheduling(bot))
