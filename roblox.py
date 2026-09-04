"""
cogs/roblox.py
Roblox account verification, using Roblox's public,
key-free APIs — no OAuth or cookies needed:
- Username lookup: users.roblox.com/v1/usernames/users
- Avatar thumbnail: thumbnails.roblox.com/v1/users/avatar-headshot

/verify links a Discord member to a Roblox account and (optionally)
auto-grants a "Verified" role. /whois looks up someone's linked account.
"""

import datetime

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, BOT_CREDIT

USERNAME_LOOKUP_URL = "https://users.roblox.com/v1/usernames/users"
AVATAR_URL = "https://thumbnails.roblox.com/v1/users/avatar-headshot"


def base_embed(title: str, description: str = None, color: int = COLOR_INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
    embed.set_footer(text=BOT_CREDIT)
    return embed


async def lookup_roblox_user(username: str) -> dict | None:
    """Look up a Roblox account by username. Returns {id, name, displayName} or None."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(USERNAME_LOOKUP_URL, json={"usernames": [username], "excludeBannedUsers": True}) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except aiohttp.ClientError:
            return None

    results = data.get("data", [])
    return results[0] if results else None


async def get_roblox_avatar_url(roblox_id: int) -> str | None:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(AVATAR_URL, params={"userIds": roblox_id, "size": "150x150", "format": "Png", "isCircular": "false"}) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except aiohttp.ClientError:
            return None

    results = data.get("data", [])
    return results[0]["imageUrl"] if results else None


class Roblox(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Link your Roblox account to your Discord account.")
    @app_commands.describe(roblox_username="Your exact Roblox username")
    async def verify(self, interaction: discord.Interaction, roblox_username: str):
        await interaction.response.defer(ephemeral=True)

        user = await lookup_roblox_user(roblox_username)
        if user is None:
            return await interaction.followup.send(
                embed=base_embed("Not Found", f"No Roblox account found for **{roblox_username}**. Double-check the spelling.", COLOR_ERROR)
            )

        timestamp = datetime.datetime.utcnow().isoformat()
        await db.add_roblox_verification(interaction.guild.id, interaction.user.id, user["id"], user["name"], timestamp)

        config = await db.get_guild_config(interaction.guild.id)
        role_granted = None
        role_id = config.get("verified_role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await interaction.user.add_roles(role, reason="Roblox verification")
                    role_granted = role
                except discord.Forbidden:
                    pass

        avatar_url = await get_roblox_avatar_url(user["id"])
        embed = base_embed("✅ Verified!", f"Linked to Roblox account **{user['name']}**" + (f"\nGranted {role_granted.mention}" if role_granted else ""), COLOR_SUCCESS)
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unverify", description="Remove your (or another member's) Roblox verification.")
    @app_commands.describe(member="Leave blank to unverify yourself; admins can unverify others")
    async def unverify(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        if target.id != interaction.user.id and not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                embed=base_embed("Missing Permissions", "You can only unverify yourself.", COLOR_ERROR), ephemeral=True
            )

        success = await db.remove_roblox_verification(interaction.guild.id, target.id)
        if not success:
            return await interaction.response.send_message(embed=base_embed("Not Verified", f"{target.mention} isn't verified.", COLOR_INFO), ephemeral=True)

        config = await db.get_guild_config(interaction.guild.id)
        role_id = config.get("verified_role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role and role in target.roles:
                try:
                    await target.remove_roles(role, reason="Roblox verification removed")
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(embed=base_embed("Unverified", f"{target.mention}'s Roblox link was removed.", COLOR_SUCCESS))

    @app_commands.command(name="whois", description="Look up a member's linked Roblox account.")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def whois(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        record = await db.get_roblox_verification(interaction.guild.id, member.id)
        if not record:
            return await interaction.response.send_message(embed=base_embed("Not Verified", f"{member.mention} hasn't verified a Roblox account.", COLOR_INFO))

        embed = base_embed(f"Roblox Account — {member}", f"**Username:** {record['roblox_username']}\n**Roblox ID:** {record['roblox_id']}\n**Verified:** <t:{int(datetime.datetime.fromisoformat(record['verified_at']).timestamp())}:R>")
        avatar_url = await get_roblox_avatar_url(record["roblox_id"])
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="verified-role", description="Set the role auto-granted when a member verifies.")
    @app_commands.describe(role="Role to grant on verification")
    @app_commands.checks.has_permissions(administrator=True)
    async def verified_role(self, interaction: discord.Interaction, role: discord.Role):
        await db.update_guild_config(interaction.guild.id, verified_role_id=role.id)
        await interaction.response.send_message(embed=base_embed("Verified Role Set", f"New verifications will now receive {role.mention}.", COLOR_SUCCESS))


async def setup(bot: commands.Bot):
    await bot.add_cog(Roblox(bot))
