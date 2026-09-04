"""
cogs/reminders.py
Timed reminders:
/remind <duration> <message> saves a reminder; a background loop checks every
30 seconds for due reminders and DMs the user (falling back to the original
channel if DMs are closed).
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database as db
from config import COLOR_INFO, COLOR_ERROR, BOT_CREDIT


def base_embed(title: str, description: str, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


def parse_duration(duration: str) -> datetime.timedelta | None:
    """Parse a short duration string like '10m', '2h', '1d', '1w' into a timedelta."""
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
    try:
        unit = duration[-1].lower()
        amount = int(duration[:-1])
        if unit not in units or amount <= 0:
            return None
        return datetime.timedelta(**{units[unit]: amount})
    except (ValueError, IndexError):
        return None


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now_iso = datetime.datetime.utcnow().isoformat()
        due = await db.get_due_reminders(now_iso)
        for reminder in due:
            await self._deliver_reminder(reminder)
            await db.delete_reminder(reminder["id"])

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    async def _deliver_reminder(self, reminder: dict):
        user = self.bot.get_user(reminder["user_id"])
        embed = base_embed("⏰ Reminder", reminder["message"] or "*(no message)*")

        delivered = False
        if user:
            try:
                await user.send(embed=embed)
                delivered = True
            except discord.Forbidden:
                pass

        if not delivered:
            channel = self.bot.get_channel(reminder["channel_id"])
            if channel:
                try:
                    mention = f"<@{reminder['user_id']}> " if reminder["guild_id"] else ""
                    await channel.send(content=mention or None, embed=embed)
                except discord.Forbidden:
                    pass

    @app_commands.command(name="remind", description="Set a reminder. e.g. /remind 10m Check the oven")
    @app_commands.describe(duration="e.g. 10m, 2h, 1d, 1w", message="What to remind you about")
    async def remind(self, interaction: discord.Interaction, duration: str, message: str):
        delta = parse_duration(duration)
        if delta is None:
            return await interaction.response.send_message(
                embed=base_embed("Invalid Duration", "Use formats like `10m`, `2h`, `1d`, `1w`.", COLOR_ERROR), ephemeral=True
            )

        remind_at = (datetime.datetime.utcnow() + delta).isoformat()
        guild_id = interaction.guild.id if interaction.guild else None
        await db.add_reminder(interaction.user.id, interaction.channel.id, guild_id, remind_at, message)

        await interaction.response.send_message(
            embed=base_embed("Reminder Set", f"I'll remind you in **{duration}**: {message}", COLOR_INFO),
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
