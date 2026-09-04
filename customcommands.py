"""
cogs/customcommands.py
Custom text commands:
Admins define a trigger word and a response; typing the bot's prefix + trigger
anywhere in the server replies with the configured response.
"""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT


def base_embed(title: str, description: str, color: int) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=BOT_CREDIT)
    return embed


class CustomCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        prefix = self.bot.command_prefix
        if isinstance(prefix, (list, tuple)):
            prefix = prefix[0]
        if not message.content.startswith(prefix):
            return

        trigger = message.content[len(prefix):].strip().split(" ")[0].lower()
        if not trigger:
            return

        response = await db.get_custom_command(message.guild.id, trigger)
        if response:
            await message.channel.send(response)

    @app_commands.command(name="customcommand-add", description="Add or update a custom command.")
    @app_commands.describe(trigger="The word that triggers this command (without the prefix)", response="What the bot should reply with")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def customcommand_add(self, interaction: discord.Interaction, trigger: str, response: str):
        trigger = trigger.lower().lstrip("!/")
        await db.add_custom_command(interaction.guild.id, trigger, response)
        await interaction.response.send_message(
            embed=base_embed("Custom Command Saved", f"`{trigger}` will now reply with your message.", COLOR_SUCCESS)
        )

    @app_commands.command(name="customcommand-remove", description="Remove a custom command.")
    @app_commands.describe(trigger="The trigger word to remove")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def customcommand_remove(self, interaction: discord.Interaction, trigger: str):
        success = await db.remove_custom_command(interaction.guild.id, trigger)
        if success:
            await interaction.response.send_message(embed=base_embed("Custom Command Removed", f"`{trigger}` was removed.", COLOR_SUCCESS))
        else:
            await interaction.response.send_message(embed=base_embed("Not Found", f"No custom command called `{trigger}`.", COLOR_ERROR), ephemeral=True)

    @app_commands.command(name="customcommand-list", description="List all custom commands in this server.")
    async def customcommand_list(self, interaction: discord.Interaction):
        commands_list = await db.list_custom_commands(interaction.guild.id)
        if not commands_list:
            return await interaction.response.send_message(embed=base_embed("Custom Commands", "None set up yet.", COLOR_INFO))
        prefix = self.bot.command_prefix if isinstance(self.bot.command_prefix, str) else self.bot.command_prefix[0]
        listing = ", ".join(f"`{prefix}{c['trigger']}`" for c in commands_list)
        await interaction.response.send_message(embed=base_embed("Custom Commands", listing, COLOR_INFO))


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomCommands(bot))
