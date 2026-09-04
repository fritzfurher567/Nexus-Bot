"""
petsystem.py
Adopt a virtual pet, feed/play with it to manage hunger and happiness.
"""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db


class PetSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pet-adopt", description="Adopt a virtual pet")
    async def pet_adopt(self, interaction: discord.Interaction, name: str, species: str):
        existing = await db.get_pet(interaction.guild_id, interaction.user.id)
        if existing:
            await interaction.response.send_message(f"You already have a pet named **{existing['name']}**.", ephemeral=True)
            return
        await db.adopt_pet(interaction.guild_id, interaction.user.id, name, species, datetime.datetime.utcnow().isoformat())
        await interaction.response.send_message(f"🐾 You adopted **{name}** the {species}!")

    @app_commands.command(name="pet-info", description="View your pet's stats")
    async def pet_info(self, interaction: discord.Interaction):
        pet = await db.get_pet(interaction.guild_id, interaction.user.id)
        if not pet:
            await interaction.response.send_message("You don't have a pet yet — use `/pet-adopt`.", ephemeral=True)
            return
        embed = discord.Embed(title=f"🐾 {pet['name']} the {pet['species']}", color=discord.Color.orange())
        embed.add_field(name="Hunger", value=f"{pet['hunger']}/100")
        embed.add_field(name="Happiness", value=f"{pet['happiness']}/100")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pet-feed", description="Feed your pet")
    async def pet_feed(self, interaction: discord.Interaction):
        pet = await db.get_pet(interaction.guild_id, interaction.user.id)
        if not pet:
            await interaction.response.send_message("You don't have a pet yet.", ephemeral=True)
            return
        await db.update_pet_stats(interaction.guild_id, interaction.user.id, pet["hunger"] + 20, pet["happiness"])
        await interaction.response.send_message(f"You fed **{pet['name']}**! 🍖")

    @app_commands.command(name="pet-play", description="Play with your pet")
    async def pet_play(self, interaction: discord.Interaction):
        pet = await db.get_pet(interaction.guild_id, interaction.user.id)
        if not pet:
            await interaction.response.send_message("You don't have a pet yet.", ephemeral=True)
            return
        await db.update_pet_stats(interaction.guild_id, interaction.user.id, pet["hunger"] - 5, pet["happiness"] + 15)
        await interaction.response.send_message(f"You played with **{pet['name']}**! 🎾")

    @app_commands.command(name="pet-release", description="Release your pet back into the wild")
    async def pet_release(self, interaction: discord.Interaction):
        pet = await db.get_pet(interaction.guild_id, interaction.user.id)
        if not pet:
            await interaction.response.send_message("You don't have a pet.", ephemeral=True)
            return
        await db.release_pet(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message(f"You released **{pet['name']}**. 🕊️")


async def setup(bot):
    await bot.add_cog(PetSystem(bot))
