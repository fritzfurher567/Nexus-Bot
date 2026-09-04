"""
roblox_extra.py
A couple of extra Roblox-group lookups that complement Roblox.py
(verify/unverify/whois) without duplicating them.
"""
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands


class RobloxExtra(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roblox-groupinfo", description="Look up a Roblox group by ID")
    async def roblox_groupinfo(self, interaction: discord.Interaction, group_id: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://groups.roblox.com/v1/groups/{group_id}") as resp:
                if resp.status != 200:
                    await interaction.followup.send("Couldn't find that group.")
                    return
                data = await resp.json()

        embed = discord.Embed(title=data.get("name", "Unknown Group"), description=data.get("description", "")[:500], color=discord.Color.blue())
        embed.add_field(name="Members", value=str(data.get("memberCount", "?")))
        embed.add_field(name="Owner", value=data.get("owner", {}).get("username", "None"))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roblox-userinfo", description="Look up a Roblox account by username")
    async def roblox_userinfo(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username], "excludeBannedUsers": False},
            ) as resp:
                data = await resp.json()

        results = data.get("data", [])
        if not results:
            await interaction.followup.send("No account found with that username.")
            return
        user = results[0]
        embed = discord.Embed(title=user["name"], color=discord.Color.blue())
        embed.add_field(name="Display Name", value=user.get("displayName", "N/A"))
        embed.add_field(name="User ID", value=str(user["id"]))
        embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user['id']}&width=150&height=150&format=png")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RobloxExtra(bot))
