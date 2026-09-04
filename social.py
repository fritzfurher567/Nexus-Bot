"""
social.py
Simple text-based social/action commands.
"""
import discord
from discord import app_commands
from discord.ext import commands


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hug", description="Hug another member")
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"🤗 {interaction.user.mention} hugs {member.mention}!")

    @app_commands.command(name="pat", description="Pat another member")
    async def pat(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"✋ {interaction.user.mention} pats {member.mention} on the head!")

    @app_commands.command(name="slap", description="Slap another member (playfully)")
    async def slap(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"👋 {interaction.user.mention} slaps {member.mention}!")

    @app_commands.command(name="highfive", description="High-five another member")
    async def highfive(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"🙌 {interaction.user.mention} high-fives {member.mention}!")

    @app_commands.command(name="compliment", description="Give another member a compliment")
    async def compliment(self, interaction: discord.Interaction, member: discord.Member):
        compliments = [
            "is doing a great job around here!",
            "has excellent taste!",
            "makes this server better just by being in it!",
        ]
        import random
        await interaction.response.send_message(f"✨ {member.mention} {random.choice(compliments)}")


async def setup(bot):
    await bot.add_cog(Social(bot))
