"""
cogs/socialalerts.py
Social media alerts:
- YouTube: polls each channel's public RSS feed (no API key required) and
  posts an embed when a new video is uploaded.
- Twitch: if TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET are set in the .env,
  polls the Helix API and posts when a streamer goes live.
  If those aren't set, Twitch commands explain what's needed and do nothing.

Note: X/Twitter alerts aren't included — X's API no longer offers a free
tier suitable for this kind of polling. The structure here (a polling task
+ a table of subscriptions) is easy to extend if you have API access.
"""

import datetime
import os
import re
import xml.etree.ElementTree as ET

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT, YOUTUBE_CHECK_INTERVAL_MINUTES, TWITCH_CHECK_INTERVAL_MINUTES

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def base_embed(title: str, description: str, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


class SocialAlerts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._twitch_token = None
        self.check_youtube.start()
        if TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET:
            self.check_twitch.start()

    def cog_unload(self):
        self.check_youtube.cancel()
        if self.check_twitch.is_running():
            self.check_twitch.cancel()

    # ---------- YOUTUBE ----------
    @tasks.loop(minutes=YOUTUBE_CHECK_INTERVAL_MINUTES)
    async def check_youtube(self):
        alerts = await db.get_youtube_alerts()
        if not alerts:
            return

        async with aiohttp.ClientSession() as session:
            for alert in alerts:
                try:
                    async with session.get(YOUTUBE_FEED_URL.format(channel_id=alert["yt_channel_id"])) as resp:
                        if resp.status != 200:
                            continue
                        text = await resp.text()
                except aiohttp.ClientError:
                    continue

                try:
                    root = ET.fromstring(text)
                    entry = root.find("atom:entry", ATOM_NS)
                    if entry is None:
                        continue
                    video_id = entry.find("yt:videoId", ATOM_NS).text
                    video_title = entry.find("atom:title", ATOM_NS).text
                    channel_name = root.find("atom:author/atom:name", ATOM_NS).text
                except (ET.ParseError, AttributeError):
                    continue

                if alert["last_video_id"] == video_id:
                    continue  # already posted this one

                await db.update_youtube_last_video(alert["id"], video_id)

                if alert["last_video_id"] is None:
                    continue  # first run for this channel — just record baseline, don't spam old video

                channel = self.bot.get_channel(alert["channel_id"])
                if channel:
                    embed = base_embed(
                        "🔴 New YouTube Upload!",
                        f"**{channel_name}** just posted: **{video_title}**\nhttps://youtu.be/{video_id}",
                        COLOR_ERROR
                    )
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass

    @check_youtube.before_loop
    async def before_check_youtube(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="youtube-alert", description="Get notified in a channel when a YouTube channel uploads.")
    @app_commands.describe(channel="Discord channel to post alerts in", youtube_channel_id="The YouTube channel ID (starts with UC...)")
    @app_commands.checks.has_permissions(administrator=True)
    async def youtube_alert(self, interaction: discord.Interaction, channel: discord.TextChannel, youtube_channel_id: str):
        if not re.match(r"^UC[\w-]{22}$", youtube_channel_id):
            return await interaction.response.send_message(
                embed=base_embed("Invalid Channel ID", "YouTube channel IDs start with `UC` and are 24 characters long. "
                                                          "You can find it in the channel's page source or via a channel-ID lookup tool.", COLOR_ERROR),
                ephemeral=True
            )
        await db.add_youtube_alert(interaction.guild.id, channel.id, youtube_channel_id)
        await interaction.response.send_message(
            embed=base_embed("YouTube Alert Added", f"New uploads will be posted in {channel.mention}.", COLOR_SUCCESS)
        )

    @app_commands.command(name="youtube-alert-remove", description="Stop alerts for a YouTube channel.")
    @app_commands.describe(youtube_channel_id="The YouTube channel ID to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def youtube_alert_remove(self, interaction: discord.Interaction, youtube_channel_id: str):
        success = await db.remove_youtube_alert(interaction.guild.id, youtube_channel_id)
        if success:
            await interaction.response.send_message(embed=base_embed("Removed", "That YouTube alert was removed.", COLOR_SUCCESS))
        else:
            await interaction.response.send_message(embed=base_embed("Not Found", "No alert matched that channel ID.", COLOR_ERROR), ephemeral=True)

    # ---------- TWITCH ----------
    async def _get_twitch_token(self, session: aiohttp.ClientSession) -> str | None:
        if self._twitch_token:
            return self._twitch_token
        try:
            async with session.post(
                "https://id.twitch.tv/oauth2/token",
                params={"client_id": TWITCH_CLIENT_ID, "client_secret": TWITCH_CLIENT_SECRET, "grant_type": "client_credentials"}
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                self._twitch_token = data.get("access_token")
                return self._twitch_token
        except aiohttp.ClientError:
            return None

    @tasks.loop(minutes=TWITCH_CHECK_INTERVAL_MINUTES)
    async def check_twitch(self):
        alerts = await db.get_twitch_alerts()
        if not alerts:
            return

        async with aiohttp.ClientSession() as session:
            token = await self._get_twitch_token(session)
            if not token:
                return
            headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}

            for alert in alerts:
                try:
                    async with session.get(
                        "https://api.twitch.tv/helix/streams",
                        params={"user_login": alert["twitch_username"]},
                        headers=headers
                    ) as resp:
                        if resp.status == 401:
                            self._twitch_token = None  # token expired, refresh next cycle
                            return
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                except aiohttp.ClientError:
                    continue

                is_live_now = len(data.get("data", [])) > 0
                was_live = bool(alert["is_live"])

                if is_live_now and not was_live:
                    stream = data["data"][0]
                    channel = self.bot.get_channel(alert["channel_id"])
                    if channel:
                        embed = base_embed(
                            "🟣 Now Live on Twitch!",
                            f"**{stream['user_name']}** is live: **{stream['title']}**\nhttps://twitch.tv/{alert['twitch_username']}",
                            0x9146FF
                        )
                        try:
                            await channel.send(embed=embed)
                        except discord.Forbidden:
                            pass

                if is_live_now != was_live:
                    await db.update_twitch_live_state(alert["id"], is_live_now)

    @check_twitch.before_loop
    async def before_check_twitch(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="twitch-alert", description="Get notified in a channel when a Twitch streamer goes live.")
    @app_commands.describe(channel="Discord channel to post alerts in", username="The Twitch username (not display name)")
    @app_commands.checks.has_permissions(administrator=True)
    async def twitch_alert(self, interaction: discord.Interaction, channel: discord.TextChannel, username: str):
        if not (TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET):
            return await interaction.response.send_message(
                embed=base_embed(
                    "Twitch Not Configured",
                    "Add `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` to your `.env` file "
                    "(free — create an app at dev.twitch.tv/console) and restart the bot to enable this.",
                    COLOR_ERROR
                ),
                ephemeral=True
            )
        await db.add_twitch_alert(interaction.guild.id, channel.id, username)
        await interaction.response.send_message(embed=base_embed("Twitch Alert Added", f"Live alerts for **{username}** will post in {channel.mention}.", COLOR_SUCCESS))

    @app_commands.command(name="twitch-alert-remove", description="Stop alerts for a Twitch streamer.")
    @app_commands.describe(username="The Twitch username to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def twitch_alert_remove(self, interaction: discord.Interaction, username: str):
        success = await db.remove_twitch_alert(interaction.guild.id, username)
        if success:
            await interaction.response.send_message(embed=base_embed("Removed", "That Twitch alert was removed.", COLOR_SUCCESS))
        else:
            await interaction.response.send_message(embed=base_embed("Not Found", "No alert matched that username.", COLOR_ERROR), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SocialAlerts(bot))
