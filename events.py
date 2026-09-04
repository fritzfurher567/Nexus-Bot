"""
cogs/events.py
Events system: schedule group activities and track who's
coming via RSVP buttons (Attending / Maybe / Declined) attached to the
event announcement.
"""

import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT

RSVP_EMOJI = {"attending": "✅", "maybe": "❓", "declined": "❌"}


def base_embed(title: str, description: str, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


async def build_event_embed(event: dict, guild: discord.Guild) -> discord.Embed:
    rsvps = await db.get_rsvps(event["id"])
    counts = {"attending": 0, "maybe": 0, "declined": 0}
    for r in rsvps:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    host = guild.get_member(event["host_id"])
    embed = discord.Embed(
        title=f"📅 {event['name']}",
        description=event["description"] or "No description provided.",
        color=COLOR_INFO,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Host", value=host.mention if host else f"<@{event['host_id']}>", inline=True)
    embed.add_field(name="When", value=event["event_time"] or "TBD", inline=True)
    embed.add_field(
        name="RSVPs",
        value=f"{RSVP_EMOJI['attending']} {counts['attending']}   {RSVP_EMOJI['maybe']} {counts['maybe']}   {RSVP_EMOJI['declined']} {counts['declined']}",
        inline=False
    )
    embed.set_footer(text=f"Event #{event['id']} • {BOT_CREDIT}")
    return embed


class EventRSVPView(discord.ui.View):
    """Persistent view attached to event announcement messages."""
    def __init__(self):
        super().__init__(timeout=None)

    async def _rsvp(self, interaction: discord.Interaction, status: str):
        footer = interaction.message.embeds[0].footer.text if interaction.message.embeds else ""
        try:
            event_id = int(footer.split("Event #")[1].split(" ")[0])
        except (IndexError, ValueError):
            return await interaction.response.send_message("Couldn't determine which event this is.", ephemeral=True)

        event = await db.get_event(event_id)
        if not event:
            return await interaction.response.send_message("This event no longer exists.", ephemeral=True)

        await db.set_rsvp(event_id, interaction.user.id, status)
        updated_embed = await build_event_embed(event, interaction.guild)
        await interaction.response.edit_message(embed=updated_embed, view=self)

    @discord.ui.button(label="Attending", style=discord.ButtonStyle.green, emoji="✅", custom_id="event_rsvp_attending")
    async def attending(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rsvp(interaction, "attending")

    @discord.ui.button(label="Maybe", style=discord.ButtonStyle.grey, emoji="❓", custom_id="event_rsvp_maybe")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rsvp(interaction, "maybe")

    @discord.ui.button(label="Can't Make It", style=discord.ButtonStyle.red, emoji="❌", custom_id="event_rsvp_declined")
    async def declined(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rsvp(interaction, "declined")


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(EventRSVPView())

    @app_commands.command(name="event-create", description="Create an event with RSVP tracking.")
    @app_commands.describe(name="Event name", description="What's happening", when="e.g. 'Sept 1, 8PM EST' — free text", channel="Where to post it (defaults to this channel)")
    @app_commands.checks.has_permissions(manage_events=True)
    async def event_create(self, interaction: discord.Interaction, name: str, description: str, when: str, channel: discord.TextChannel = None):
        target = channel or interaction.channel
        created_at = datetime.datetime.utcnow().isoformat()
        event_id = await db.create_event(interaction.guild.id, name, description, interaction.user.id, when, target.id, created_at)

        event = await db.get_event(event_id)
        embed = await build_event_embed(event, interaction.guild)
        message = await target.send(embed=embed, view=EventRSVPView())
        await db.set_event_message(event_id, message.id)

        await interaction.response.send_message(embed=base_embed("Event Created", f"Posted in {target.mention}.", COLOR_SUCCESS), ephemeral=True)

    @app_commands.command(name="event-list", description="Show upcoming events.")
    async def event_list(self, interaction: discord.Interaction):
        events = await db.get_upcoming_events(interaction.guild.id)
        if not events:
            return await interaction.response.send_message(embed=base_embed("Upcoming Events", "No events scheduled.", COLOR_INFO))
        lines = [f"**#{e['id']} — {e['name']}** — {e['event_time'] or 'TBD'}" for e in events]
        await interaction.response.send_message(embed=base_embed("📅 Upcoming Events", "\n".join(lines), COLOR_INFO))

    @app_commands.command(name="event-attendance", description="See who RSVP'd to an event.")
    @app_commands.describe(event_id="The event ID (shown in /event-list)")
    async def event_attendance(self, interaction: discord.Interaction, event_id: int):
        event = await db.get_event(event_id)
        if not event or event["guild_id"] != interaction.guild.id:
            return await interaction.response.send_message(embed=base_embed("Not Found", f"No event with ID #{event_id}.", COLOR_ERROR), ephemeral=True)

        rsvps = await db.get_rsvps(event_id)
        grouped = {"attending": [], "maybe": [], "declined": []}
        for r in rsvps:
            grouped.setdefault(r["status"], []).append(f"<@{r['user_id']}>")

        embed = base_embed(f"Attendance — {event['name']}", None, COLOR_INFO)
        embed.add_field(name=f"{RSVP_EMOJI['attending']} Attending ({len(grouped['attending'])})", value=", ".join(grouped["attending"]) or "None", inline=False)
        embed.add_field(name=f"{RSVP_EMOJI['maybe']} Maybe ({len(grouped['maybe'])})", value=", ".join(grouped["maybe"]) or "None", inline=False)
        embed.add_field(name=f"{RSVP_EMOJI['declined']} Declined ({len(grouped['declined'])})", value=", ".join(grouped["declined"]) or "None", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
