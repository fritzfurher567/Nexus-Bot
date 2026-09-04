"""
northwind_duty.py
Northwind-specific ops commands: duty clock in/out with hour tracking,
uniform/formation inspections, patrol logs, and a modal-based recruitment
application flow with accept/deny buttons for staff.
"""
import datetime
import json

import discord
from discord import app_commands
from discord.ext import commands

import database as db


def _fmt_duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m"


class ApplicationModal(discord.ui.Modal, title="Northwind Recruitment Application"):
    age = discord.ui.TextInput(label="Age", required=True, max_length=3)
    experience = discord.ui.TextInput(label="Relevant experience", style=discord.TextStyle.paragraph, required=True)
    why_join = discord.ui.TextInput(label="Why do you want to join?", style=discord.TextStyle.paragraph, required=True)
    timezone = discord.ui.TextInput(label="Timezone", required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        cog: NorthwindDuty = interaction.client.get_cog("NorthwindDuty")
        answers = {
            "Age": str(self.age),
            "Experience": str(self.experience),
            "Why join": str(self.why_join),
            "Timezone": str(self.timezone),
        }
        await cog.submit_application(interaction, answers)


class ApplicationReviewView(discord.ui.View):
    def __init__(self, application_id: int):
        super().__init__(timeout=None)
        self.application_id = application_id
        self.accept.custom_id = f"application:accept:{application_id}"
        self.deny.custom_id = f"application:deny:{application_id}"

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog: NorthwindDuty = interaction.client.get_cog("NorthwindDuty")
        await cog.resolve_application(interaction, self.application_id, "accepted")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog: NorthwindDuty = interaction.client.get_cog("NorthwindDuty")
        await cog.resolve_application(interaction, self.application_id, "denied")


class NorthwindDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---- Duty clock in/out ----

    @app_commands.command(name="duty-clockin", description="Clock in for a duty/patrol shift")
    async def duty_clockin(self, interaction: discord.Interaction):
        existing = await db.get_open_duty_session(interaction.guild_id, interaction.user.id)
        if existing:
            await interaction.response.send_message("You're already clocked in.", ephemeral=True)
            return
        await db.clock_in(interaction.guild_id, interaction.user.id, datetime.datetime.utcnow().isoformat())
        await interaction.response.send_message(f"🟢 {interaction.user.mention} clocked in.")

    @app_commands.command(name="duty-clockout", description="Clock out of your current shift")
    async def duty_clockout(self, interaction: discord.Interaction):
        session = await db.get_open_duty_session(interaction.guild_id, interaction.user.id)
        if not session:
            await interaction.response.send_message("You're not clocked in.", ephemeral=True)
            return
        now = datetime.datetime.utcnow()
        await db.clock_out(session["id"], now.isoformat())
        started = datetime.datetime.fromisoformat(session["clock_in"])
        minutes = int((now - started).total_seconds() // 60)
        await interaction.response.send_message(
            f"🔴 {interaction.user.mention} clocked out. Shift length: **{_fmt_duration(minutes)}**"
        )

    @app_commands.command(name="duty-hours", description="View total logged duty hours for a member")
    async def duty_hours(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        sessions = await db.get_duty_hours(interaction.guild_id, member.id)
        total_minutes = 0
        for s in sessions:
            started = datetime.datetime.fromisoformat(s["clock_in"])
            ended = datetime.datetime.fromisoformat(s["clock_out"])
            total_minutes += int((ended - started).total_seconds() // 60)
        embed = discord.Embed(
            title=f"⏱️ Duty Hours — {member.display_name}",
            description=f"Total logged: **{_fmt_duration(total_minutes)}** across {len(sessions)} session(s)",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    # ---- Inspections ----

    @app_commands.command(name="inspection", description="Log a uniform/formation inspection result")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.choices(result=[
        app_commands.Choice(name="Pass", value="pass"),
        app_commands.Choice(name="Fail", value="fail"),
        app_commands.Choice(name="Conditional Pass", value="conditional"),
    ])
    async def inspection(self, interaction: discord.Interaction, member: discord.Member, result: app_commands.Choice[str], notes: str = ""):
        await db.add_inspection(
            interaction.guild_id, member.id, interaction.user.id, result.value, notes,
            datetime.datetime.utcnow().isoformat()
        )
        color = {"pass": discord.Color.green(), "fail": discord.Color.red(), "conditional": discord.Color.orange()}[result.value]
        embed = discord.Embed(title="📋 Inspection Logged", color=color)
        embed.add_field(name="Member", value=member.mention)
        embed.add_field(name="Result", value=result.name)
        embed.add_field(name="Inspector", value=interaction.user.mention)
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)
        await interaction.response.send_message(embed=embed)

    # ---- Patrol logs ----

    @app_commands.command(name="patrol-log", description="Record a patrol report")
    async def patrol_log(self, interaction: discord.Interaction, route: str, duration_minutes: int, incidents: str = "None"):
        await db.add_patrol_log(
            interaction.guild_id, interaction.user.id, route, incidents, duration_minutes,
            datetime.datetime.utcnow().isoformat()
        )
        embed = discord.Embed(title="🚓 Patrol Log", color=discord.Color.dark_teal())
        embed.add_field(name="Officer", value=interaction.user.mention)
        embed.add_field(name="Route", value=route)
        embed.add_field(name="Duration", value=_fmt_duration(duration_minutes))
        embed.add_field(name="Incidents", value=incidents, inline=False)
        await interaction.response.send_message(embed=embed)

    # ---- Applications ----

    @app_commands.command(name="applications-channel", description="[Admin] Set where applications get reviewed")
    @app_commands.checks.has_permissions(administrator=True)
    async def applications_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.set_applications_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Applications will be reviewed in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="apply", description="Submit a recruitment application")
    async def apply(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplicationModal())

    async def submit_application(self, interaction: discord.Interaction, answers: dict):
        config = await db.get_applications_config(interaction.guild_id)
        if not config["review_channel_id"]:
            await interaction.response.send_message("Applications aren't set up yet. Ask an admin to run /applications-channel.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(config["review_channel_id"])
        if not channel:
            await interaction.response.send_message("Configured review channel no longer exists.", ephemeral=True)
            return

        timestamp = datetime.datetime.utcnow().isoformat()
        application_id = await db.add_application(interaction.guild_id, interaction.user.id, json.dumps(answers), timestamp)

        embed = discord.Embed(title=f"New Application — #{application_id}", color=discord.Color.blurple())
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        for k, v in answers.items():
            embed.add_field(name=k, value=v, inline=False)

        view = ApplicationReviewView(application_id)
        self.bot.add_view(view)
        msg = await channel.send(embed=embed, view=view)
        await db.set_application_message(application_id, channel.id, msg.id)

        await interaction.response.send_message("Application submitted! Staff will review it soon.", ephemeral=True)

    async def resolve_application(self, interaction: discord.Interaction, application_id: int, status: str):
        application = await db.get_application(application_id)
        if not application:
            await interaction.response.send_message("Application not found.", ephemeral=True)
            return

        await db.set_application_status(application_id, status, interaction.user.id)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green() if status == "accepted" else discord.Color.red()
        embed.title = f"Application #{application_id} — {status.title()}"
        embed.set_footer(text=f"Reviewed by {interaction.user}")
        await interaction.response.edit_message(embed=embed, view=None)

        applicant = interaction.guild.get_member(application["user_id"])
        if applicant:
            try:
                await applicant.send(f"Your Northwind application was **{status}** by {interaction.user}.")
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(NorthwindDuty(bot))
