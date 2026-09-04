"""
cogs/groupops.py
Group management tools:
- Awards: staff can award members with a title + reason, logged and viewable
- Leave of Absence (LOA): members request time away with a date range and
  reason; staff approve/deny via buttons; /loa-list shows who's currently away.
Useful for any server that tracks member activity/roles closely — staff
teams, gaming clans, or Roblox groups.
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT


def base_embed(title: str, description: str, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


class LOAReviewView(discord.ui.View):
    """Persistent view attached to LOA request posts in the review channel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji="✅", custom_id="loa_approve_button")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolve(interaction, "approved", COLOR_SUCCESS)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, emoji="❌", custom_id="loa_deny_button")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolve(interaction, "denied", COLOR_ERROR)

    async def _resolve(self, interaction: discord.Interaction, status: str, color: int):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have permission to review LOA requests.", ephemeral=True)

        # The LOA id was embedded in the original message footer text
        footer = interaction.message.embeds[0].footer.text if interaction.message.embeds else ""
        try:
            loa_id = int(footer.split("LOA #")[1].split(" ")[0])
        except (IndexError, ValueError):
            return await interaction.response.send_message("Couldn't determine which request this is.", ephemeral=True)

        loa = await db.get_loa_request(loa_id)
        if not loa:
            return await interaction.response.send_message("That request no longer exists.", ephemeral=True)

        await db.set_loa_status(loa_id, status, interaction.user.id)

        updated_embed = interaction.message.embeds[0]
        updated_embed.color = color
        updated_embed.add_field(name="Status", value=f"{status.title()} by {interaction.user.mention}", inline=False)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=updated_embed, view=self)

        member = interaction.guild.get_member(loa["user_id"])
        if member:
            try:
                await member.send(embed=base_embed(f"LOA {status.title()}", f"Your leave request ({loa['start_date']} to {loa['end_date']}) was **{status}**.", color))
            except discord.Forbidden:
                pass


class GroupOps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(LOAReviewView())

    # ---------- AWARDS ----------
    @app_commands.command(name="award", description="Give a member an award/commendation.")
    @app_commands.describe(member="The member to award", title="Name of the award", reason="Why they're receiving it")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def award(self, interaction: discord.Interaction, member: discord.Member, title: str, reason: str = "No reason provided"):
        timestamp = datetime.datetime.utcnow().isoformat()
        award_id = await db.add_award(interaction.guild.id, member.id, interaction.user.id, title, reason, timestamp)

        embed = base_embed("🏅 Award Given", f"**{member}** received **{title}**\n**Reason:** {reason}\n**Awarded by:** {interaction.user.mention}", COLOR_SUCCESS)
        await interaction.response.send_message(embed=embed)

        config = await db.get_guild_config(interaction.guild.id)
        channel_id = config.get("awards_channel")
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel and channel.id != interaction.channel.id:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        try:
            await member.send(embed=base_embed("🏅 You Received an Award!", f"**{title}** in {interaction.guild.name}\n**Reason:** {reason}", COLOR_SUCCESS))
        except discord.Forbidden:
            pass

    @app_commands.command(name="awards", description="View a member's award history.")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def awards(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        records = await db.get_awards(interaction.guild.id, member.id)
        if not records:
            return await interaction.response.send_message(embed=base_embed("Awards", f"{member.mention} has no awards yet.", COLOR_INFO))

        lines = [f"**{r['title']}** — {r['reason']} (<t:{int(datetime.datetime.fromisoformat(r['timestamp']).timestamp())}:D>)" for r in records]
        await interaction.response.send_message(embed=base_embed(f"🏅 Awards — {member}", "\n".join(lines), COLOR_SUCCESS))

    @app_commands.command(name="awards-channel", description="Set the channel where awards are announced.")
    @app_commands.describe(channel="Channel to post award announcements in")
    @app_commands.checks.has_permissions(administrator=True)
    async def awards_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.update_guild_config(interaction.guild.id, awards_channel=channel.id)
        await interaction.response.send_message(embed=base_embed("Awards Channel Set", f"Awards will now also be posted in {channel.mention}.", COLOR_SUCCESS))

    # ---------- LEAVE OF ABSENCE ----------
    @app_commands.command(name="loa-request", description="Request a leave of absence.")
    @app_commands.describe(start_date="e.g. 2026-09-01", end_date="e.g. 2026-09-10", reason="Why you need time away")
    async def loa_request(self, interaction: discord.Interaction, start_date: str, end_date: str, reason: str):
        config = await db.get_guild_config(interaction.guild.id)
        channel_id = config.get("loa_channel")
        if not channel_id or not interaction.guild.get_channel(channel_id):
            return await interaction.response.send_message(
                embed=base_embed("Not Configured", "Ask an admin to set up `/loa-channel` first.", COLOR_ERROR), ephemeral=True
            )

        requested_at = datetime.datetime.utcnow().isoformat()
        loa_id = await db.add_loa_request(interaction.guild.id, interaction.user.id, start_date, end_date, reason, requested_at)

        review_channel = interaction.guild.get_channel(channel_id)
        embed = base_embed(
            "📋 New LOA Request",
            f"**Member:** {interaction.user.mention}\n**From:** {start_date}\n**To:** {end_date}\n**Reason:** {reason}",
            COLOR_INFO
        )
        embed.set_footer(text=f"LOA #{loa_id} • {BOT_CREDIT}")
        await review_channel.send(embed=embed, view=LOAReviewView())

        await interaction.response.send_message(embed=base_embed("Request Submitted", "Your LOA request has been sent for review.", COLOR_SUCCESS), ephemeral=True)

    @app_commands.command(name="loa-list", description="List all currently approved leaves of absence.")
    async def loa_list(self, interaction: discord.Interaction):
        active = await db.get_active_loas(interaction.guild.id)
        if not active:
            return await interaction.response.send_message(embed=base_embed("Active LOAs", "No one is currently on an approved leave of absence.", COLOR_INFO))

        lines = []
        for loa in active:
            member = interaction.guild.get_member(loa["user_id"])
            name = member.mention if member else f"<@{loa['user_id']}>"
            lines.append(f"{name} — {loa['start_date']} to {loa['end_date']}")

        await interaction.response.send_message(embed=base_embed("📋 Active LOAs", "\n".join(lines), COLOR_INFO))

    @app_commands.command(name="loa-channel", description="Set the channel where LOA requests are sent for staff review.")
    @app_commands.describe(channel="Channel where staff will approve/deny requests")
    @app_commands.checks.has_permissions(administrator=True)
    async def loa_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.update_guild_config(interaction.guild.id, loa_channel=channel.id)
        await interaction.response.send_message(embed=base_embed("LOA Channel Set", f"LOA requests will be reviewed in {channel.mention}.", COLOR_SUCCESS))


async def setup(bot: commands.Bot):
    await bot.add_cog(GroupOps(bot))
