"""
birthdays.py
Members set their birthday; a daily background task announces matches.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database as db


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start()

    def cog_unload(self):
        self.check_birthdays.cancel()

    @app_commands.command(name="birthday-set", description="Set your birthday (month/day only, no year stored)")
    async def birthday_set(self, interaction: discord.Interaction, month: app_commands.Range[int, 1, 12], day: app_commands.Range[int, 1, 31]):
        try:
            datetime.date(2000, month, day)  # leap year, just to validate day-of-month
        except ValueError:
            await interaction.response.send_message("That's not a real date.", ephemeral=True)
            return
        await db.set_birthday(interaction.guild_id, interaction.user.id, month, day)
        await interaction.response.send_message(f"Birthday set to {month}/{day}.", ephemeral=True)

    @app_commands.command(name="birthdays", description="List upcoming birthdays this server has on file")
    async def birthdays(self, interaction: discord.Interaction):
        rows = await db.get_all_birthdays(interaction.guild_id)
        if not rows:
            await interaction.response.send_message("No birthdays on file yet.", ephemeral=True)
            return
        lines = []
        for r in rows:
            member = interaction.guild.get_member(r["user_id"])
            name = member.display_name if member else f"User {r['user_id']}"
            lines.append(f"**{name}** — {r['month']}/{r['day']}")
        embed = discord.Embed(title="🎂 Birthdays", description="\n".join(lines), color=discord.Color.pink())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="birthday-channel", description="[Admin] Set the channel birthday announcements post to")
    @app_commands.checks.has_permissions(administrator=True)
    async def birthday_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.update_guild_config(interaction.guild_id, birthday_channel=channel.id)
        await interaction.response.send_message(f"Birthday announcements will post in {channel.mention}.", ephemeral=True)

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        today = datetime.date.today()
        for guild in self.bot.guilds:
            user_ids = await db.get_birthdays_on(guild.id, today.month, today.day)
            if not user_ids:
                continue
            config = await db.get_guild_config(guild.id)
            channel_id = config.get("birthday_channel") or config.get("welcome_channel")
            channel = guild.get_channel(channel_id) if channel_id else None
            if not channel:
                continue
            for uid in user_ids:
                member = guild.get_member(uid)
                if member:
                    await channel.send(f"🎉🎂 Happy birthday, {member.mention}!")

    @check_birthdays.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Birthdays(bot))
