"""
cogs/utility.py
General utility & info commands: help, ping, server info, user info,
avatar, and a /credits command crediting the original creator.
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import COLOR_INFO, BOT_CREDIT


def base_embed(title: str, description: str = None, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color,
                           timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=base_embed("Pong! 🏓", f"Latency: **{round(self.bot.latency * 1000)}ms**"))

    @app_commands.command(name="credits", description="See who made this bot.")
    async def credits(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=base_embed("Credits", BOT_CREDIT))

    @app_commands.command(name="serverinfo", description="Show information about this server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = base_embed(guild.name)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=str(guild.owner), inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Text Channels", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="Voice Channels", value=str(len(guild.voice_channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show information about a member.")
    @app_commands.describe(member="The member to look up (defaults to you)")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = base_embed(str(member))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a member's avatar.")
    @app_commands.describe(member="The member to look up (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = base_embed(f"{member}'s Avatar")
        embed.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="List all available commands.")
    async def help(self, interaction: discord.Interaction):
        embed = base_embed("📖 Command List")
        embed.add_field(
            name="🛡️ Moderation",
            value="`/kick` `/ban` `/unban` `/timeout` `/untimeout` `/warn` `/warnings` "
                  "`/clearwarnings` `/removewarning` `/purge` `/lock` `/unlock` `/lockdown` "
                  "`/slowmode` `/nickname` `/addrole` `/removerole` `/setmodlog`",
            inline=False
        )
        embed.add_field(
            name="🤖 Auto-Mod",
            value="`/automod-bannedwords` `/automod-toggle` `/automod-mentionlimit`",
            inline=False
        )
        embed.add_field(
            name="📋 Server Logging",
            value="`/setserverlog`",
            inline=False
        )
        embed.add_field(
            name="🎫 Tickets",
            value="`/ticket-setup` `/ticket-panel` `/ticket-add` `/ticket-remove` "
                  "`/ticket-priority` `/ticket-close`",
            inline=False
        )
        embed.add_field(
            name="👋 Welcome/Goodbye",
            value="`/welcome-setup` `/goodbye-setup` `/welcome-dm` `/goodbye-dm`",
            inline=False
        )
        embed.add_field(
            name="⭐ Leveling",
            value="`/rank` `/leaderboard` `/setlevelrole` `/removelevelrole` `/levelup-channel`",
            inline=False
        )
        embed.add_field(
            name="🎭 Reaction Roles",
            value="`/reactionrole-add` `/reactionrole-remove`",
            inline=False
        )
        embed.add_field(
            name="💬 Custom Commands",
            value="`/customcommand-add` `/customcommand-remove` `/customcommand-list`",
            inline=False
        )
        embed.add_field(
            name="⏰ Reminders",
            value="`/remind`",
            inline=False
        )
        embed.add_field(
            name="🪙 Economy",
            value="`/balance` `/daily` `/work` `/pay` `/economy-leaderboard` "
                  "`/shop` `/buy` `/shop-add` `/shop-remove`",
            inline=False
        )
        embed.add_field(
            name="📡 Social Alerts",
            value="`/youtube-alert` `/youtube-alert-remove` `/twitch-alert` `/twitch-alert-remove`",
            inline=False
        )
        embed.add_field(
            name="🎨 Embeds",
            value="`/embed` `/say`",
            inline=False
        )
        embed.add_field(
            name="ℹ️ Utility",
            value="`/ping` `/serverinfo` `/userinfo` `/avatar` `/credits` `/help`",
            inline=False
        )
        
         
        embed.add_field(
            name="Need More Help??",
            value="Visit The nil Website For More Support",
            inline=False
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
