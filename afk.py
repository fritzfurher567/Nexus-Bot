"""
afk.py
Set an AFK status; get auto-replied-to-pingers and auto-cleared when you
next talk.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="afk", description="Set yourself as AFK")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        await db.set_afk(interaction.guild_id, interaction.user.id, reason, datetime.datetime.utcnow().isoformat())
        await interaction.response.send_message(f"You're now AFK: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Clear the author's own AFK if they talk again
        own_afk = await db.get_afk(message.guild.id, message.author.id)
        if own_afk:
            await db.clear_afk(message.guild.id, message.author.id)
            try:
                await message.channel.send(f"Welcome back, {message.author.mention} — I removed your AFK.", delete_after=8)
            except discord.Forbidden:
                pass

        # Notify if any pinged user is AFK
        for user in message.mentions:
            afk_row = await db.get_afk(message.guild.id, user.id)
            if afk_row:
                since = datetime.datetime.fromisoformat(afk_row["since"])
                await message.channel.send(
                    f"💤 {user.display_name} is AFK: {afk_row['reason']} (since <t:{int(since.timestamp())}:R>)"
                )


async def setup(bot):
    await bot.add_cog(AFK(bot))
