"""
snipe.py
Shows the last deleted / edited message per channel. In-memory only
(no DB needed - snipes are meant to be short-lived).
"""
import discord
from discord import app_commands
from discord.ext import commands

MAX_AGE_SECONDS = 300  # only allow sniping messages from the last 5 minutes


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted: dict[int, dict] = {}  # channel_id -> {content, author, time}
        self.edited: dict[int, dict] = {}   # channel_id -> {before, after, author, time}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        self.deleted[message.channel.id] = {
            "content": message.content,
            "author": message.author,
            "time": discord.utils.utcnow(),
            "attachments": [a.url for a in message.attachments],
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        self.edited[before.channel.id] = {
            "before": before.content,
            "after": after.content,
            "author": before.author,
            "time": discord.utils.utcnow(),
        }

    @app_commands.command(name="snipe", description="Show the last deleted message in this channel")
    async def snipe(self, interaction: discord.Interaction):
        entry = self.deleted.get(interaction.channel_id)
        if not entry or (discord.utils.utcnow() - entry["time"]).total_seconds() > MAX_AGE_SECONDS:
            await interaction.response.send_message("Nothing recent to snipe here.", ephemeral=True)
            return
        embed = discord.Embed(description=entry["content"] or "*[no text content]*", color=discord.Color.orange())
        embed.set_author(name=str(entry["author"]), icon_url=entry["author"].display_avatar.url)
        embed.set_footer(text=f"Deleted {discord.utils.format_dt(entry['time'], 'R')}")
        if entry["attachments"]:
            embed.set_image(url=entry["attachments"][0])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="editsnipe", description="Show the last edited message in this channel")
    async def editsnipe(self, interaction: discord.Interaction):
        entry = self.edited.get(interaction.channel_id)
        if not entry or (discord.utils.utcnow() - entry["time"]).total_seconds() > MAX_AGE_SECONDS:
            await interaction.response.send_message("Nothing recent to editsnipe here.", ephemeral=True)
            return
        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=str(entry["author"]), icon_url=entry["author"].display_avatar.url)
        embed.add_field(name="Before", value=entry["before"] or "*[empty]*", inline=False)
        embed.add_field(name="After", value=entry["after"] or "*[empty]*", inline=False)
        embed.set_footer(text=f"Edited {discord.utils.format_dt(entry['time'], 'R')}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Snipe(bot))
