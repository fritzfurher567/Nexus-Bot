"""
textutils.py
Small text-manipulation utility commands.
"""
import random

import discord
from discord import app_commands
from discord.ext import commands


class TextUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="choose", description="Pick a random item from a comma-separated list")
    async def choose(self, interaction: discord.Interaction, options: str):
        items = [o.strip() for o in options.split(",") if o.strip()]
        if len(items) < 2:
            await interaction.response.send_message("Give me at least 2 comma-separated options.", ephemeral=True)
            return
        await interaction.response.send_message(f"🎯 I choose: **{random.choice(items)}**")

    @app_commands.command(name="reversetext", description="Reverse a string of text")
    async def reversetext(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(text[::-1])

    @app_commands.command(name="mocktext", description="Convert text to sPoNgEbOb CaSe")
    async def mocktext(self, interaction: discord.Interaction, text: str):
        result = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))
        await interaction.response.send_message(result)

    @app_commands.command(name="randomcolor", description="Generate a random hex color")
    async def randomcolor(self, interaction: discord.Interaction):
        color = discord.Color.random()
        hex_code = f"#{color.value:06X}"
        embed = discord.Embed(title=hex_code, color=color)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TextUtils(bot))
