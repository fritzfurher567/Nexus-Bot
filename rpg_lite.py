"""
rpg_lite.py
Lightweight gather-and-earn commands (Tatsu-style) that pay out pounds
with their own cooldowns — separate flavor from /work and /crime.
"""
import random
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db

CURRENCY = "£"
COOLDOWN_MIN = 20


class RPGLite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cooldowns: dict[tuple[int, int, str], datetime.datetime] = {}

    async def _do_activity(self, interaction: discord.Interaction, activity: str, low: int, high: int, flavor: list[str]):
        key = (interaction.guild_id, interaction.user.id, activity)
        now = datetime.datetime.utcnow()
        last = self._cooldowns.get(key)
        if last and (now - last) < datetime.timedelta(minutes=COOLDOWN_MIN):
            remaining = datetime.timedelta(minutes=COOLDOWN_MIN) - (now - last)
            await interaction.response.send_message(f"Still recovering. Try again in {remaining.seconds // 60}m.", ephemeral=True)
            return
        self._cooldowns[key] = now

        earned = random.randint(low, high)
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + earned)
        await interaction.response.send_message(f"{random.choice(flavor)} You earned **{CURRENCY}{earned}**.")

    @app_commands.command(name="fish", description="Go fishing for pounds")
    async def fish(self, interaction: discord.Interaction):
        await self._do_activity(interaction, "fish", 30, 150, ["🎣 You caught a big one!", "🎣 Nice catch!", "🎣 Reeled in a haul!"])

    @app_commands.command(name="hunt", description="Go hunting for pounds")
    async def hunt(self, interaction: discord.Interaction):
        await self._do_activity(interaction, "hunt", 40, 180, ["🏹 Successful hunt!", "🏹 You tracked down some game!"])

    @app_commands.command(name="mine", description="Go mining for pounds")
    async def mine(self, interaction: discord.Interaction):
        await self._do_activity(interaction, "mine", 50, 200, ["⛏️ Struck a good vein!", "⛏️ Found some valuable ore!"])

    @app_commands.command(name="craft", description="Craft goods to sell for pounds")
    async def craft(self, interaction: discord.Interaction):
        await self._do_activity(interaction, "craft", 60, 220, ["🔨 Crafted something sellable!", "🔨 Nice work at the bench!"])

    @app_commands.command(name="adventure", description="Go on a small adventure for pounds (highest risk/reward of the bunch)")
    async def adventure(self, interaction: discord.Interaction):
        key = (interaction.guild_id, interaction.user.id, "adventure")
        now = datetime.datetime.utcnow()
        last = self._cooldowns.get(key)
        if last and (now - last) < datetime.timedelta(minutes=COOLDOWN_MIN):
            remaining = datetime.timedelta(minutes=COOLDOWN_MIN) - (now - last)
            await interaction.response.send_message(f"Still recovering. Try again in {remaining.seconds // 60}m.", ephemeral=True)
            return
        self._cooldowns[key] = now

        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if random.random() < 0.7:
            earned = random.randint(100, 400)
            await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + earned)
            await interaction.response.send_message(f"🗺️ The adventure paid off! You found **{CURRENCY}{earned}**.")
        else:
            lost = min(random.randint(50, 150), row["balance"])
            await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - lost)
            await interaction.response.send_message(f"🗺️ Rough trip — you lost **{CURRENCY}{lost}** in gear.")


async def setup(bot):
    await bot.add_cog(RPGLite(bot))
